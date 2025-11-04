"""
Celery tasks for generating visualizations.
"""

from celery import shared_task
import logging
import os

logger = logging.getLogger(__name__)


@shared_task
def generate_default_visualizations(analysis_id: int):
    """
    Generate default visualizations for an analysis.

    Args:
        analysis_id: ID of the Analysis object
    """
    from apps.analysis.models import Analysis
    from .models import Visualization
    from .generators import (
        generate_similarity_heatmap,
        generate_correlation_matrix,
        generate_gps_map
    )

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        logger.info(f"Generating default visualizations for {analysis.name}")

        # Generate similarity heatmap
        try:
            heatmap_path = generate_similarity_heatmap(analysis)
            if heatmap_path:
                Visualization.objects.create(
                    analysis=analysis,
                    viz_type='heatmap',
                    title=f"Similarity Heatmap - {analysis.name}",
                    file_path=heatmap_path,
                    file_format='png',
                    created_by=analysis.created_by
                )
                logger.info("Generated similarity heatmap")
        except Exception as e:
            logger.error(f"Error generating heatmap: {e}")

        # Generate correlation matrix
        try:
            corr_path = generate_correlation_matrix(analysis)
            if corr_path:
                Visualization.objects.create(
                    analysis=analysis,
                    viz_type='correlation',
                    title=f"Correlation Matrix - {analysis.name}",
                    file_path=corr_path,
                    file_format='png',
                    created_by=analysis.created_by
                )
                logger.info("Generated correlation matrix")
        except Exception as e:
            logger.error(f"Error generating correlation matrix: {e}")

        # Generate GPS map if images have GPS data
        if analysis.dataset.images.filter(metadata__has_gps=True).exists():
            try:
                map_path = generate_gps_map(analysis)
                if map_path:
                    Visualization.objects.create(
                        analysis=analysis,
                        viz_type='map',
                        title=f"GPS Map - {analysis.name}",
                        file_path=map_path,
                        file_format='html',
                        created_by=analysis.created_by
                    )
                    logger.info("Generated GPS map")
            except Exception as e:
                logger.error(f"Error generating GPS map: {e}")

        logger.info(f"Default visualizations complete for {analysis.name}")

    except Exception as e:
        logger.error(f"Error generating visualizations for analysis {analysis_id}: {e}", exc_info=True)


@shared_task
def generate_custom_visualization(analysis_id: int, viz_type: str, config: dict):
    """
    Generate a custom visualization based on parameters.

    Args:
        analysis_id: ID of the Analysis object
        viz_type: Type of visualization to generate
        config: Configuration dictionary for the visualization
    """
    from apps.analysis.models import Analysis
    from .models import Visualization
    from . import generators

    try:
        analysis = Analysis.objects.get(id=analysis_id)
        logger.info(f"Generating {viz_type} for {analysis.name}")

        # Map viz_type to generator function
        generator_map = {
            'heatmap': generators.generate_similarity_heatmap,
            'correlation': generators.generate_correlation_matrix,
            'map': generators.generate_gps_map,
            'violin': generators.generate_violin_plot,
            'location_corr': generators.generate_location_correlation,
        }

        generator_func = generator_map.get(viz_type)
        if not generator_func:
            raise ValueError(f"Unknown visualization type: {viz_type}")

        # Generate visualization
        file_path = generator_func(analysis, **config)

        if file_path:
            Visualization.objects.create(
                analysis=analysis,
                viz_type=viz_type,
                title=config.get('title', f"{viz_type} - {analysis.name}"),
                file_path=file_path,
                file_format=config.get('format', 'png'),
                config=config,
                created_by=analysis.created_by
            )
            logger.info(f"Generated {viz_type} visualization")

    except Exception as e:
        logger.error(f"Error generating {viz_type} for analysis {analysis_id}: {e}", exc_info=True)


@shared_task
def export_analysis_results(export_job_id: int):
    """
    Export analysis results to file.

    Args:
        export_job_id: ID of the ExportJob object
    """
    from .models import ExportJob
    from .exporters import export_to_json, export_to_csv, export_to_zip

    try:
        export_job = ExportJob.objects.get(id=export_job_id)
        export_job.status = 'processing'
        export_job.save()

        analysis = export_job.analysis
        logger.info(f"Exporting {analysis.name} as {export_job.format}")

        # Map format to exporter function
        exporter_map = {
            'json': export_to_json,
            'csv': export_to_csv,
            'zip': export_to_zip,
        }

        exporter_func = exporter_map.get(export_job.format)
        if not exporter_func:
            raise ValueError(f"Unknown export format: {export_job.format}")

        # Export results
        file_path = exporter_func(
            analysis,
            include_images=export_job.include_images,
            include_visualizations=export_job.include_visualizations
        )

        if file_path:
            export_job.file_path = file_path
            export_job.file_size = os.path.getsize(file_path)
            export_job.status = 'completed'
            export_job.save()
            logger.info(f"Export complete: {file_path}")
        else:
            raise ValueError("Export failed - no file generated")

    except Exception as e:
        logger.error(f"Error exporting results for job {export_job_id}: {e}", exc_info=True)
        try:
            export_job = ExportJob.objects.get(id=export_job_id)
            export_job.status = 'failed'
            export_job.error_message = str(e)
            export_job.save()
        except:
            pass
