"""
Heatmap generator for similarity visualizations.
"""

from typing import Dict, Any
from io import BytesIO
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt

from .base import BaseGenerator


class HeatmapGenerator(BaseGenerator):
    """
    Generate similarity heatmaps showing image-text similarities.

    Creates a color-coded matrix where:
    - Rows = Images
    - Columns = Text prompts
    - Colors = Similarity scores (0-1)
    """

    viz_type = 'heatmap'
    default_format = 'png'
    supported_formats = ['png', 'svg', 'pdf']

    def get_title(self) -> str:
        """Get default title for this visualization."""
        return f"{self.analysis.name} - Similarity Heatmap"

    def generate(self) -> bytes:
        """
        Generate the similarity heatmap.

        Returns:
            PNG/SVG/PDF bytes of the heatmap

        Raises:
            ValueError: If insufficient data
        """
        # Get data
        data = self.get_data()
        self.validate_data(data)

        # Extract configuration
        colormap = self.config.get('colormap', 'viridis')
        figsize = self.config.get('figsize', None)
        dpi = self.config.get('dpi', 100)
        show_values = self.config.get('show_values', False)

        # Prepare data for plotting
        image_names = list(data.keys())

        # Get prompts from first image (all should have same prompts)
        text_prompts = list(data[image_names[0]].keys())

        # Create similarity matrix
        similarity_matrix = np.zeros((len(image_names), len(text_prompts)))
        for i, img_name in enumerate(image_names):
            for j, prompt in enumerate(text_prompts):
                similarity_matrix[i, j] = data[img_name].get(prompt, 0.0)

        # Calculate figure size if not provided
        if figsize is None:
            # Base width on number of prompts, height on number of images
            width = max(10, len(text_prompts) * 1.5)
            height = max(6, len(image_names) * 0.4 + 2)
            figsize = (width, height)

        # Create the plot
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Create heatmap
        im = ax.imshow(similarity_matrix, cmap=colormap, aspect='auto',
                       vmin=0, vmax=1, interpolation='nearest')

        # Add colorbar
        cbar = fig.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('Similarity Score', rotation=-90, va="bottom", fontsize=10)

        # Set ticks and labels
        ax.set_xticks(np.arange(len(text_prompts)))
        ax.set_yticks(np.arange(len(image_names)))
        ax.set_xticklabels(text_prompts, fontsize=9)
        ax.set_yticklabels(image_names, fontsize=8)

        # Rotate x-axis labels for readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
                rotation_mode="anchor")

        # Add text annotations if requested
        if show_values:
            for i in range(len(image_names)):
                for j in range(len(text_prompts)):
                    value = similarity_matrix[i, j]
                    # Use white text for dark colors, black for light colors
                    text_color = 'white' if value < 0.5 else 'black'
                    ax.text(j, i, f'{value:.2f}', ha="center", va="center",
                           color=text_color, fontsize=7)

        # Add labels
        ax.set_xlabel('Text Prompts', fontsize=11)
        ax.set_ylabel('Images', fontsize=11)

        # Add title
        title = self.config.get('title', self.get_title())
        ax.set_title(title, fontsize=13, pad=15)

        # Adjust layout to prevent label cutoff
        fig.tight_layout()

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
        Validate heatmap data.

        Args:
            data: Dictionary of image_name -> {prompt: score}

        Raises:
            ValueError: If data is insufficient
        """
        super().validate_data(data)

        # Check that we have at least one prompt
        first_image = list(data.keys())[0]
        prompts = list(data[first_image].keys())

        if not prompts:
            raise ValueError("No text prompts found for visualization")

        # Verify all images have the same prompts
        for img_name, img_data in data.items():
            if set(img_data.keys()) != set(prompts):
                raise ValueError(
                    f"Image '{img_name}' has different prompts than others"
                )
