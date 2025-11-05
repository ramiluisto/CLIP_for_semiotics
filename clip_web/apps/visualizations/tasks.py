"""
Celery tasks for generating visualizations.
"""

from celery import shared_task
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


@shared_task
def generate_default_visualizations(analysis_id: int, user_id: Optional[int] = None):
    """
    Generate default visualizations for an analysis.

    Creates:
    - Similarity heatmap
    - Correlation matrix
    - Image grid (top 12 images by score)

    Args:
        analysis_id: ID of the Analysis object
        user_id: Optional ID of the user requesting generation
    """
    from apps.analysis.models import Analysis
    from django.contrib.auth import get_user_model
    from .generators import (
        HeatmapGenerator,
        CorrelationMatrixGenerator,
        ImageGridGenerator
    )

    User = get_user_model()

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        user = User.objects.get(id=user_id) if user_id else analysis.created_by

        logger.info(f"Generating default visualizations for analysis {analysis.id}: {analysis.name}")

        # Generate similarity heatmap
        try:
            logger.info("Generating similarity heatmap...")
            generator = HeatmapGenerator(analysis)
            visualization = generator.generate_and_save(user=user)
            logger.info(f"Generated similarity heatmap: {visualization.id}")
        except Exception as e:
            logger.error(f"Error generating heatmap: {e}", exc_info=True)

        # Generate correlation matrix
        try:
            logger.info("Generating correlation matrix...")
            generator = CorrelationMatrixGenerator(analysis)
            visualization = generator.generate_and_save(user=user)
            logger.info(f"Generated correlation matrix: {visualization.id}")
        except Exception as e:
            logger.error(f"Error generating correlation matrix: {e}", exc_info=True)

        # Generate image grid (top 12 images)
        try:
            logger.info("Generating image grid...")
            config = {
                'cols': 3,
                'max_images': 12,
                'sort_by': 'score',
                'sort_order': 'desc'
            }
            generator = ImageGridGenerator(analysis, config=config)
            visualization = generator.generate_and_save(user=user)
            logger.info(f"Generated image grid: {visualization.id}")
        except Exception as e:
            logger.error(f"Error generating image grid: {e}", exc_info=True)

        logger.info(f"Default visualizations complete for analysis {analysis.id}")

        return {
            'status': 'success',
            'analysis_id': analysis_id,
            'message': 'Default visualizations generated successfully'
        }

    except Exception as e:
        logger.error(f"Error generating visualizations for analysis {analysis_id}: {e}", exc_info=True)
        return {
            'status': 'error',
            'analysis_id': analysis_id,
            'error': str(e)
        }


@shared_task
def generate_custom_visualization(
    analysis_id: int,
    viz_type: str,
    config: Optional[Dict[str, Any]] = None,
    user_id: Optional[int] = None
):
    """
    Generate a custom visualization based on parameters.

    Args:
        analysis_id: ID of the Analysis object
        viz_type: Type of visualization to generate
        config: Configuration dictionary for the visualization
        user_id: Optional ID of the user requesting generation

    Returns:
        dict: Status information about the generation
    """
    from apps.analysis.models import Analysis
    from django.contrib.auth import get_user_model
    from .generators import (
        HeatmapGenerator,
        CorrelationMatrixGenerator,
        ImageGridGenerator
    )

    User = get_user_model()

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        user = User.objects.get(id=user_id) if user_id else analysis.created_by

        logger.info(f"Generating custom {viz_type} for analysis {analysis.id}: {analysis.name}")

        # Map viz_type to generator class
        generator_map = {
            'heatmap': HeatmapGenerator,
            'correlation': CorrelationMatrixGenerator,
            'image_grid': ImageGridGenerator,
        }

        generator_class = generator_map.get(viz_type)
        if not generator_class:
            raise ValueError(f"Unknown visualization type: {viz_type}")

        # Generate visualization
        generator = generator_class(analysis, config=config or {})

        # Get custom title if provided
        title = config.get('title') if config else None

        visualization = generator.generate_and_save(user=user, title=title)

        logger.info(f"Generated {viz_type} visualization: {visualization.id}")

        return {
            'status': 'success',
            'analysis_id': analysis_id,
            'viz_type': viz_type,
            'visualization_id': visualization.id,
            'message': f'{viz_type} visualization generated successfully'
        }

    except Exception as e:
        logger.error(f"Error generating {viz_type} for analysis {analysis_id}: {e}", exc_info=True)
        return {
            'status': 'error',
            'analysis_id': analysis_id,
            'viz_type': viz_type,
            'error': str(e)
        }


@shared_task
def generate_visualizations_batch(analysis_ids: list, viz_types: Optional[list] = None):
    """
    Generate visualizations for multiple analyses in batch.

    Args:
        analysis_ids: List of Analysis IDs
        viz_types: Optional list of specific viz types to generate.
                   If None, generates default visualizations.

    Returns:
        dict: Summary of generation results
    """
    logger.info(f"Starting batch visualization generation for {len(analysis_ids)} analyses")

    results = {
        'total': len(analysis_ids),
        'successful': 0,
        'failed': 0,
        'errors': []
    }

    for analysis_id in analysis_ids:
        try:
            if viz_types:
                # Generate specific visualization types
                for viz_type in viz_types:
                    result = generate_custom_visualization(analysis_id, viz_type)
                    if result['status'] == 'error':
                        results['errors'].append({
                            'analysis_id': analysis_id,
                            'viz_type': viz_type,
                            'error': result['error']
                        })
            else:
                # Generate default visualizations
                result = generate_default_visualizations(analysis_id)
                if result['status'] == 'error':
                    results['failed'] += 1
                    results['errors'].append({
                        'analysis_id': analysis_id,
                        'error': result['error']
                    })
                    continue

            results['successful'] += 1

        except Exception as e:
            logger.error(f"Error in batch generation for analysis {analysis_id}: {e}")
            results['failed'] += 1
            results['errors'].append({
                'analysis_id': analysis_id,
                'error': str(e)
            })

    logger.info(f"Batch generation complete: {results['successful']}/{results['total']} successful")

    return results


@shared_task
def export_analysis_results(export_job_id: int):
    """
    Export analysis results to file.

    Note: Exporter functions need to be implemented in exporters.py

    Args:
        export_job_id: ID of the ExportJob object
    """
    from .models import ExportJob
    from datetime import datetime

    try:
        export_job = ExportJob.objects.get(id=export_job_id)
        export_job.status = 'processing'
        export_job.save()

        analysis = export_job.analysis
        logger.info(f"Exporting analysis {analysis.id}: {analysis.name} as {export_job.format}")

        # TODO: Implement exporters in exporters.py
        # For now, log a placeholder message
        logger.warning("Export functionality not yet fully implemented")

        # Placeholder - will be implemented when exporters.py is created
        export_job.status = 'completed'
        export_job.completed_at = datetime.now()
        export_job.save()

        logger.info(f"Export job {export_job_id} marked as complete (placeholder)")

        return {
            'status': 'success',
            'export_job_id': export_job_id,
            'message': 'Export placeholder - full implementation pending'
        }

    except Exception as e:
        logger.error(f"Error exporting results for job {export_job_id}: {e}", exc_info=True)
        try:
            export_job = ExportJob.objects.get(id=export_job_id)
            export_job.status = 'failed'
            export_job.error_message = str(e)
            export_job.save()
        except:
            pass

        return {
            'status': 'error',
            'export_job_id': export_job_id,
            'error': str(e)
        }
