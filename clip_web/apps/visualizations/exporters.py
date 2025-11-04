"""
Exporters for analysis results.
"""

import json
import csv
import zipfile
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


def export_to_json(analysis, include_images=False, include_visualizations=True):
    """
    Export analysis results to JSON.

    Args:
        analysis: Analysis object
        include_images: Whether to include image data
        include_visualizations: Whether to include visualization metadata

    Returns:
        Path to generated file
    """
    try:
        # Build export data
        data = {
            'analysis': {
                'id': analysis.id,
                'name': analysis.name,
                'description': analysis.description,
                'created_at': analysis.created_at.isoformat(),
                'model_name': analysis.model_name,
            },
            'text_prompts': [
                {'text': p.text, 'order': p.order}
                for p in analysis.text_prompts.all().order_by('order')
            ],
            'results': []
        }

        # Add results
        for result in analysis.results.select_related('image', 'text_prompt').all():
            result_data = {
                'image': result.image.original_filename,
                'text_prompt': result.text_prompt.text,
                'similarity_score': result.similarity_score,
            }

            if hasattr(result.image, 'gps_data'):
                gps = result.image.gps_data
                result_data['gps'] = {
                    'latitude': float(gps.latitude),
                    'longitude': float(gps.longitude),
                }

            data['results'].append(result_data)

        # Save to file
        output_dir = os.path.join(settings.MEDIA_ROOT, 'exports', str(analysis.id))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'{analysis.slug}_results.json')

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        return output_path

    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}", exc_info=True)
        return None


def export_to_csv(analysis, include_images=False, include_visualizations=True):
    """
    Export analysis results to CSV.

    Args:
        analysis: Analysis object

    Returns:
        Path to generated file
    """
    try:
        # Prepare data
        prompts = list(analysis.text_prompts.all().order_by('order'))
        images = list(analysis.dataset.images.all())

        # Save to file
        output_dir = os.path.join(settings.MEDIA_ROOT, 'exports', str(analysis.id))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'{analysis.project.slug}_{analysis.name.replace(" ", "_")}_results.csv')

        with open(output_path, 'w', newline='') as f:
            # Create header
            fieldnames = ['image_filename']
            for prompt in prompts:
                fieldnames.append(f'similarity_{prompt.text}')
            fieldnames.extend(['latitude', 'longitude'])

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # Write rows
            for image in images:
                row = {'image_filename': image.original_filename}

                # Get similarities for this image
                for prompt in prompts:
                    result = analysis.results.filter(image=image, text_prompt=prompt).first()
                    score = result.similarity_score if result else 0.0
                    row[f'similarity_{prompt.text}'] = score

                # Add GPS if available
                if hasattr(image, 'gps_data'):
                    row['latitude'] = float(image.gps_data.latitude)
                    row['longitude'] = float(image.gps_data.longitude)
                else:
                    row['latitude'] = ''
                    row['longitude'] = ''

                writer.writerow(row)

        return output_path

    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}", exc_info=True)
        return None


def export_to_zip(analysis, include_images=False, include_visualizations=True):
    """
    Export analysis results as a ZIP archive.

    Args:
        analysis: Analysis object
        include_images: Whether to include original images
        include_visualizations: Whether to include visualizations

    Returns:
        Path to generated file
    """
    try:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'exports', str(analysis.id))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f'{analysis.project.slug}_{analysis.name.replace(" ", "_")}_export.zip')

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add JSON results
            json_path = export_to_json(analysis)
            if json_path and os.path.exists(json_path):
                zipf.write(json_path, 'results.json')

            # Add CSV results
            csv_path = export_to_csv(analysis)
            if csv_path and os.path.exists(csv_path):
                zipf.write(csv_path, 'results.csv')

            # Add visualizations
            if include_visualizations:
                for viz in analysis.visualizations.all():
                    if viz.file_path and os.path.exists(viz.file_path):
                        zipf.write(
                            viz.file_path,
                            f'visualizations/{os.path.basename(viz.file_path)}'
                        )

            # Add images (optional)
            if include_images:
                for image in analysis.dataset.images.all():
                    if image.file and os.path.exists(image.file.path):
                        zipf.write(
                            image.file.path,
                            f'images/{image.original_filename}'
                        )

        return output_path

    except Exception as e:
        logger.error(f"Error exporting to ZIP: {e}", exc_info=True)
        return None
