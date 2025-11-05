"""
Correlation matrix generator for concept relationships.
"""

from typing import Dict, Any
from io import BytesIO
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt

from .base import BaseGenerator


class CorrelationMatrixGenerator(BaseGenerator):
    """
    Generate correlation matrices showing relationships between text prompts.

    Calculates Pearson correlation between different text prompts across all images.
    High correlation means two concepts tend to co-occur in the same images.

    Creates a symmetric matrix where:
    - Rows/Columns = Text prompts
    - Values = Correlation coefficient (-1 to +1)
    - +1 = Perfect positive correlation
    - -1 = Perfect negative correlation
    - 0 = No correlation
    """

    viz_type = 'correlation'
    default_format = 'png'
    supported_formats = ['png', 'svg', 'pdf']

    def get_title(self) -> str:
        """Get default title for this visualization."""
        return f"{self.analysis.name} - Concept Correlation Matrix"

    def generate(self) -> bytes:
        """
        Generate the correlation matrix.

        Returns:
            PNG/SVG/PDF bytes of the correlation matrix

        Raises:
            ValueError: If insufficient data or prompts
        """
        # Get data
        data = self.get_data()
        self.validate_data(data)

        # Extract configuration
        colormap = self.config.get('colormap', 'coolwarm')
        figsize = self.config.get('figsize', None)
        dpi = self.config.get('dpi', 100)
        show_values = self.config.get('show_values', True)  # Default to showing values

        # Get all unique prompts
        prompts = list(data[list(data.keys())[0]].keys())

        # Build DataFrame with similarity scores
        # Each row is an image, each column is a prompt
        df_data = []
        for img_name, img_scores in data.items():
            row = {}
            for prompt in prompts:
                row[prompt] = img_scores.get(prompt, np.nan)
            df_data.append(row)

        df = pd.DataFrame(df_data)

        # Calculate correlation matrix
        corr_matrix = df.corr()

        # Calculate figure size if not provided
        if figsize is None:
            # Base size on number of prompts
            size = max(8, len(prompts) * 0.8)
            figsize = (size, size)

        # Create the plot
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Create heatmap
        im = ax.imshow(corr_matrix, cmap=colormap, aspect='auto',
                       vmin=-1, vmax=1, interpolation='nearest')

        # Add colorbar
        cbar = fig.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('Correlation Coefficient', rotation=-90, va="bottom", fontsize=10)

        # Set ticks and labels
        ax.set_xticks(np.arange(len(prompts)))
        ax.set_yticks(np.arange(len(prompts)))
        ax.set_xticklabels(prompts, fontsize=9)
        ax.set_yticklabels(prompts, fontsize=9)

        # Rotate x-axis labels for readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
                rotation_mode="anchor")

        # Add correlation values to cells if requested
        if show_values:
            for i in range(len(prompts)):
                for j in range(len(prompts)):
                    value = corr_matrix.iloc[i, j]
                    if not np.isnan(value):
                        # Use white text for extreme values, black for mid-range
                        text_color = 'white' if abs(value) > 0.5 else 'black'
                        ax.text(j, i, f'{value:.2f}', ha="center", va="center",
                               color=text_color, fontsize=8)

        # Add title
        title = self.config.get('title', self.get_title())
        ax.set_title(title, fontsize=13, pad=15)

        # Add explanation subtitle
        subtitle = "How concepts co-occur across images (1 = always together, -1 = never together)"
        fig.text(0.5, 0.02, subtitle, ha='center', fontsize=9,
                style='italic', color='gray')

        # Adjust layout to prevent label cutoff
        fig.tight_layout(rect=[0, 0.04, 1, 1])  # Leave room for subtitle

        # Save to bytes
        buffer = BytesIO()
        fig.savefig(buffer, format=self.file_format, bbox_inches='tight',
                   dpi=dpi, facecolor='white')
        buffer.seek(0)

        # Clean up
        plt.close(fig)

        return buffer.getvalue()

    def validate_data(self, data: Dict[str, Any]) -> None:
        """
        Validate correlation matrix data.

        Args:
            data: Dictionary of image_name -> {prompt: score}

        Raises:
            ValueError: If data is insufficient
        """
        super().validate_data(data)

        # Need at least 2 prompts for correlation
        first_image = list(data.keys())[0]
        prompts = list(data[first_image].keys())

        if len(prompts) < 2:
            raise ValueError(
                "Need at least 2 text prompts to calculate correlations"
            )

        # Need at least 2 images for meaningful correlation
        if len(data) < 2:
            raise ValueError(
                "Need at least 2 images to calculate meaningful correlations"
            )

        # Verify all images have the same prompts
        for img_name, img_data in data.items():
            if set(img_data.keys()) != set(prompts):
                raise ValueError(
                    f"Image '{img_name}' has different prompts than others"
                )
