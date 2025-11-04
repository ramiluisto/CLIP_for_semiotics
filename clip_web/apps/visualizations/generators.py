"""
Visualization generators adapted from src/visualization.py
"""

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


def generate_similarity_heatmap(analysis, **kwargs):
    """
    Generate a similarity heatmap for an analysis.

    Args:
        analysis: Analysis object

    Returns:
        Path to generated file
    """
    try:
        # Get results
        results = analysis.results.select_related('image', 'text_prompt').all()

        if not results.exists():
            return None

        # Build similarity matrix
        images = list(analysis.dataset.images.all())
        prompts = list(analysis.text_prompts.all().order_by('order'))

        image_names = [img.original_filename for img in images]
        prompt_texts = [p.text for p in prompts]

        similarity_matrix = np.zeros((len(images), len(prompts)))

        for result in results:
            img_idx = next((i for i, img in enumerate(images) if img.id == result.image_id), None)
            prompt_idx = next((i for i, p in enumerate(prompts) if p.id == result.text_prompt_id), None)

            if img_idx is not None and prompt_idx is not None:
                similarity_matrix[img_idx, prompt_idx] = result.similarity_score

        # Create heatmap
        fig, ax = plt.subplots(figsize=(12, max(6, len(images) * 0.3)))
        im = ax.imshow(similarity_matrix, cmap='viridis', aspect='auto')

        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Similarity Score", rotation=-90, va="bottom")

        # Set ticks and labels
        ax.set_xticks(np.arange(len(prompt_texts)))
        ax.set_yticks(np.arange(len(image_names)))
        ax.set_xticklabels(prompt_texts)
        ax.set_yticklabels(image_names)

        # Rotate x labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # Title
        ax.set_title(f"Similarity Heatmap - {analysis.name}")
        fig.tight_layout()

        # Save
        output_dir = os.path.join(settings.MEDIA_ROOT, 'visualizations', str(analysis.id))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'heatmap.png')

        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        return output_path

    except Exception as e:
        logger.error(f"Error generating heatmap: {e}", exc_info=True)
        return None


def generate_correlation_matrix(analysis, **kwargs):
    """
    Generate a correlation matrix between text prompts.

    Args:
        analysis: Analysis object

    Returns:
        Path to generated file
    """
    try:
        # Get results
        prompts = list(analysis.text_prompts.all().order_by('order'))

        # Build dataframe
        data = {}
        for prompt in prompts:
            scores = list(
                analysis.results.filter(text_prompt=prompt).values_list('similarity_score', flat=True)
            )
            data[prompt.text] = scores

        df = pd.DataFrame(data)

        if df.empty:
            return None

        # Calculate correlation
        corr_matrix = df.corr()

        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')

        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Correlation", rotation=-90, va="bottom")

        # Set ticks
        prompt_texts = [p.text for p in prompts]
        ax.set_xticks(np.arange(len(prompt_texts)))
        ax.set_yticks(np.arange(len(prompt_texts)))
        ax.set_xticklabels(prompt_texts)
        ax.set_yticklabels(prompt_texts)

        # Rotate x labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

        # Add correlation values
        for i in range(len(prompt_texts)):
            for j in range(len(prompt_texts)):
                value = corr_matrix.iloc[i, j]
                if not np.isnan(value):
                    text_color = "white" if abs(value) > 0.5 else "black"
                    ax.text(j, i, f"{value:.2f}", ha="center", va="center", color=text_color)

        # Title
        ax.set_title(f"Concept Correlation Matrix - {analysis.name}")
        fig.tight_layout()

        # Save
        output_dir = os.path.join(settings.MEDIA_ROOT, 'visualizations', str(analysis.id))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'correlation.png')

        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)

        return output_path

    except Exception as e:
        logger.error(f"Error generating correlation matrix: {e}", exc_info=True)
        return None


def generate_gps_map(analysis, **kwargs):
    """
    Generate an interactive GPS map.

    Args:
        analysis: Analysis object

    Returns:
        Path to generated file
    """
    try:
        import folium

        # Get images with GPS data
        images_with_gps = analysis.dataset.images.filter(
            metadata__has_gps=True
        ).select_related('gps_data')

        if not images_with_gps.exists():
            return None

        # Calculate map center
        gps_data_list = [img.gps_data for img in images_with_gps if hasattr(img, 'gps_data')]
        if not gps_data_list:
            return None

        avg_lat = sum(float(gps.latitude) for gps in gps_data_list) / len(gps_data_list)
        avg_lon = sum(float(gps.longitude) for gps in gps_data_list) / len(gps_data_list)

        # Create map
        m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

        # Add markers
        for img in images_with_gps:
            if hasattr(img, 'gps_data'):
                gps = img.gps_data
                folium.Marker(
                    location=[float(gps.latitude), float(gps.longitude)],
                    popup=img.original_filename,
                    tooltip=img.original_filename
                ).add_to(m)

        # Save
        output_dir = os.path.join(settings.MEDIA_ROOT, 'visualizations', str(analysis.id))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'map.html')

        m.save(output_path)

        return output_path

    except Exception as e:
        logger.error(f"Error generating GPS map: {e}", exc_info=True)
        return None


def generate_violin_plot(analysis, **kwargs):
    """
    Generate a violin plot showing score distributions.

    Args:
        analysis: Analysis object

    Returns:
        Path to generated file
    """
    # TODO: Implement violin plot
    return None


def generate_location_correlation(analysis, **kwargs):
    """
    Generate location correlation plots.

    Args:
        analysis: Analysis object

    Returns:
        Path to generated file
    """
    # TODO: Implement location correlation
    return None
