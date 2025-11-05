"""
Image grid generator for displaying images with similarity scores.
"""

from typing import Dict, Any, Optional
from io import BytesIO
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
from PIL import Image as PILImage

from .base import BaseGenerator


class ImageGridGenerator(BaseGenerator):
    """
    Generate image grids showing images sorted by similarity scores.

    Creates a grid layout displaying images with their similarity scores.
    Useful for visual inspection of which images match specific concepts.

    Configuration options:
    - cols: Number of columns (default: 3)
    - max_images: Maximum images to display (default: 12)
    - prompt: Specific prompt to show scores for (default: show highest score)
    - sort_by: 'score' (default) or 'name'
    - sort_order: 'desc' (default) or 'asc'
    """

    viz_type = 'image_grid'
    default_format = 'png'
    supported_formats = ['png', 'pdf']

    def get_title(self) -> str:
        """Get default title for this visualization."""
        prompt = self.config.get('prompt')
        if prompt:
            return f"{self.analysis.name} - Images for '{prompt}'"
        return f"{self.analysis.name} - Image Grid"

    def generate(self) -> bytes:
        """
        Generate the image grid.

        Returns:
            PNG/PDF bytes of the image grid

        Raises:
            ValueError: If insufficient data or images
        """
        # Get data
        data = self.get_data()
        self.validate_data(data)

        # Extract configuration
        cols = self.config.get('cols', 3)
        max_images = self.config.get('max_images', 12)
        target_prompt = self.config.get('prompt')
        sort_by = self.config.get('sort_by', 'score')
        sort_order = self.config.get('sort_order', 'desc')
        dpi = self.config.get('dpi', 100)

        # Get all images with their scores
        image_data = []
        for img_name, scores in data.items():
            # Get the Image model instance to access file path
            from apps.images.models import Image as ImageModel
            try:
                img_obj = ImageModel.objects.filter(
                    dataset__analyses=self.analysis,
                    file_path__icontains=img_name
                ).first()

                if not img_obj:
                    # Try matching just the filename
                    img_obj = ImageModel.objects.filter(
                        dataset__analyses=self.analysis,
                        file_path__endswith=img_name
                    ).first()

                if img_obj:
                    # Determine score to use for sorting
                    if target_prompt and target_prompt in scores:
                        score = scores[target_prompt]
                        prompt_label = target_prompt
                    else:
                        # Use highest score
                        score = max(scores.values())
                        prompt_label = max(scores, key=scores.get)

                    image_data.append({
                        'name': img_name,
                        'path': img_obj.file_path.path,
                        'score': score,
                        'prompt': prompt_label,
                        'all_scores': scores
                    })
            except Exception as e:
                self.logger.warning(f"Could not load image {img_name}: {e}")
                continue

        if not image_data:
            raise ValueError("No valid images found for grid generation")

        # Sort images
        if sort_by == 'score':
            reverse = (sort_order == 'desc')
            image_data.sort(key=lambda x: x['score'], reverse=reverse)
        else:  # sort by name
            reverse = (sort_order == 'desc')
            image_data.sort(key=lambda x: x['name'], reverse=reverse)

        # Limit to max_images
        image_data = image_data[:max_images]

        # Calculate grid dimensions
        n_images = len(image_data)
        rows = (n_images + cols - 1) // cols

        # Calculate figure size (wider for more columns, taller for more rows)
        fig_width = cols * 4
        fig_height = rows * 3.5
        figsize = self.config.get('figsize', (fig_width, fig_height))

        # Create figure
        fig = plt.figure(figsize=figsize, dpi=dpi)

        # Add overall title
        title = self.config.get('title', self.get_title())
        fig.suptitle(title, fontsize=16, y=0.98)

        # Add images to grid
        for i, img_info in enumerate(image_data):
            # Create subplot
            ax = fig.add_subplot(rows, cols, i + 1)

            # Load and display image
            try:
                img = PILImage.open(img_info['path'])

                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                ax.imshow(img)

                # Create title with score
                img_title = f"{os.path.basename(img_info['name'])}\n"
                img_title += f"Score: {img_info['score']:.3f} ({img_info['prompt']})"

                ax.set_title(img_title, fontsize=9, pad=5)

            except Exception as e:
                self.logger.warning(f"Error displaying image {img_info['path']}: {e}")
                # Show error placeholder
                ax.text(
                    0.5, 0.5,
                    f"Error loading\n{os.path.basename(img_info['name'])}",
                    ha='center', va='center',
                    fontsize=10, color='red'
                )

            # Remove axis ticks
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_frame_on(True)

        # Remove empty subplots if grid not completely filled
        for i in range(n_images, rows * cols):
            ax = fig.add_subplot(rows, cols, i + 1)
            ax.axis('off')

        # Adjust layout
        fig.tight_layout(rect=[0, 0, 1, 0.97])  # Leave room for suptitle

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
        Validate image grid data.

        Args:
            data: Dictionary of image_name -> {prompt: score}

        Raises:
            ValueError: If data is insufficient
        """
        super().validate_data(data)

        # Check that we have at least one image
        if len(data) == 0:
            raise ValueError("No images found for grid visualization")

        # Check that images have scores
        first_image = list(data.keys())[0]
        if not data[first_image]:
            raise ValueError("No similarity scores found for images")

        # Validate specific prompt if provided
        target_prompt = self.config.get('prompt')
        if target_prompt:
            # Check if at least one image has this prompt
            has_prompt = any(
                target_prompt in img_scores
                for img_scores in data.values()
            )
            if not has_prompt:
                raise ValueError(
                    f"Prompt '{target_prompt}' not found in any image scores"
                )
