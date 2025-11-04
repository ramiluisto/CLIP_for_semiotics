"""
Celery tasks for CLIP analysis processing.
"""

from celery import shared_task, current_task
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_analysis_job(self, analysis_id: int):
    """
    Main task for processing a CLIP analysis job.

    Args:
        analysis_id: ID of the Analysis object

    Returns:
        Dictionary with processing results
    """
    from .models import Analysis, SimilarityResult
    from .clip_service import get_clip_service

    try:
        # Get analysis object
        analysis = Analysis.objects.select_related('dataset').get(id=analysis_id)

        # Update status
        analysis.status = 'processing'
        analysis.started_at = timezone.now()
        analysis.celery_task_id = self.request.id
        analysis.save()

        logger.info(f"Starting analysis {analysis.name} (ID: {analysis_id})")

        # Get images and text prompts
        images = analysis.dataset.images.all()
        text_prompts = analysis.text_prompts.all().order_by('order')
        text_list = [prompt.text for prompt in text_prompts]

        total_images = images.count()
        analysis.total_images = total_images
        analysis.save()

        if total_images == 0:
            raise ValueError("No images in dataset")

        if len(text_list) == 0:
            raise ValueError("No text prompts defined")

        # Initialize CLIP service
        clip_service = get_clip_service()
        logger.info(f"Using CLIP model: {clip_service.get_model_name()} on {clip_service.get_device()}")

        # Process each image
        results_to_create = []
        for idx, image in enumerate(images):
            # Update progress
            progress = int((idx / total_images) * 100)
            analysis.progress_percentage = progress
            analysis.images_processed = idx
            analysis.save(update_fields=['progress_percentage', 'images_processed'])

            # Update Celery task state
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': idx,
                    'total': total_images,
                    'percentage': progress,
                    'image': image.original_filename
                }
            )

            # Process image with CLIP
            try:
                similarities = clip_service.compare_image_with_texts(
                    image.file.path,
                    text_list
                )

                # Prepare results for bulk creation
                for text_prompt in text_prompts:
                    score = similarities.get(text_prompt.text, 0.0)
                    results_to_create.append(
                        SimilarityResult(
                            analysis=analysis,
                            image=image,
                            text_prompt=text_prompt,
                            similarity_score=score
                        )
                    )

                # Bulk create results every 50 images
                if len(results_to_create) >= 50:
                    SimilarityResult.objects.bulk_create(results_to_create)
                    results_to_create = []

                logger.debug(f"Processed image {idx+1}/{total_images}: {image.original_filename}")

            except Exception as e:
                logger.error(f"Error processing image {image.id}: {e}")
                continue

        # Create any remaining results
        if results_to_create:
            SimilarityResult.objects.bulk_create(results_to_create)

        # Update analysis as completed
        analysis.completed_at = timezone.now()
        analysis.processing_time_seconds = (
            analysis.completed_at - analysis.started_at
        ).total_seconds()
        analysis.status = 'completed'
        analysis.progress_percentage = 100
        analysis.images_processed = total_images
        analysis.save()

        logger.info(f"Completed analysis {analysis.name} in {analysis.processing_time_seconds:.2f}s")

        # Trigger post-processing
        post_process_analysis.delay(analysis_id)

        return {
            'status': 'completed',
            'images_processed': analysis.images_processed,
            'processing_time': analysis.processing_time_seconds
        }

    except Analysis.DoesNotExist:
        logger.error(f"Analysis {analysis_id} not found")
        raise

    except Exception as e:
        logger.error(f"Error processing analysis {analysis_id}: {e}", exc_info=True)

        # Update analysis as failed
        try:
            analysis = Analysis.objects.get(id=analysis_id)
            analysis.status = 'failed'
            analysis.error_message = str(e)
            analysis.save()
        except:
            pass

        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def post_process_analysis(analysis_id: int):
    """
    Post-processing tasks after analysis completes.
    - Normalize GPS coordinates
    - Cluster locations
    - Generate default visualizations
    """
    from .models import Analysis
    from apps.images.models import GPSData
    from apps.visualizations.tasks import generate_default_visualizations

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        logger.info(f"Post-processing analysis {analysis.name}")

        # Get images with GPS data
        dataset_images = analysis.dataset.images.filter(metadata__has_gps=True)

        if dataset_images.exists():
            # Normalize GPS coordinates
            gps_data_list = GPSData.objects.filter(image__in=dataset_images)

            if gps_data_list.exists():
                # Normalize coordinates
                coordinates = [(gps.latitude, gps.longitude) for gps in gps_data_list]
                from apps.images.gps_service import gps_service
                normalized = gps_service.normalize_coordinates(coordinates)

                # Update GPS data with normalized coordinates
                for gps_data, (norm_lat, norm_lon) in zip(gps_data_list, normalized):
                    gps_data.normalized_latitude = norm_lat
                    gps_data.normalized_longitude = norm_lon

                GPSData.objects.bulk_update(
                    gps_data_list,
                    ['normalized_latitude', 'normalized_longitude']
                )

                logger.info(f"Normalized coordinates for {len(gps_data_list)} images")

                # TODO: Implement clustering
                # cluster_locations_task.delay(analysis_id)

        # Generate default visualizations
        generate_default_visualizations.delay(analysis_id)

        logger.info(f"Post-processing complete for analysis {analysis.name}")

    except Exception as e:
        logger.error(f"Error in post-processing for analysis {analysis_id}: {e}", exc_info=True)


@shared_task(bind=True)
def extract_image_metadata_task(self, image_id: int):
    """
    Extract metadata from an uploaded image.

    Args:
        image_id: ID of the Image object
    """
    from apps.images.models import Image
    from apps.images.utils import extract_image_metadata, create_thumbnail

    try:
        image = Image.objects.get(id=image_id)
        logger.info(f"Extracting metadata for image {image.original_filename}")

        # Extract metadata
        extract_image_metadata(image)

        # Create thumbnail
        create_thumbnail(image)

        logger.info(f"Metadata extraction complete for {image.original_filename}")

    except Image.DoesNotExist:
        logger.error(f"Image {image_id} not found")
    except Exception as e:
        logger.error(f"Error extracting metadata for image {image_id}: {e}", exc_info=True)


@shared_task
def cleanup_old_results(days=30):
    """
    Periodic task to cleanup old analysis results.

    Args:
        days: Delete results older than this many days
    """
    from datetime import timedelta
    from .models import Analysis

    try:
        cutoff_date = timezone.now() - timedelta(days=days)

        # Get old completed analyses
        old_analyses = Analysis.objects.filter(
            status='completed',
            completed_at__lt=cutoff_date
        )

        count = old_analyses.count()
        old_analyses.delete()

        logger.info(f"Cleaned up {count} old analyses")

    except Exception as e:
        logger.error(f"Error in cleanup task: {e}", exc_info=True)
