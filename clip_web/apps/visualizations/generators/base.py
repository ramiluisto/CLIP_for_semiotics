"""
Base generator class for all visualizations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import os
import logging

from django.conf import settings
from django.core.files.base import ContentFile
from apps.analysis.models import Analysis
from apps.visualizations.models import Visualization

logger = logging.getLogger(__name__)


class BaseGenerator(ABC):
    """
    Abstract base class for all visualization generators.

    Provides common functionality for:
    - File management
    - Model creation
    - Error handling
    - Configuration management
    """

    # Override in subclasses
    viz_type: str = None
    default_format: str = 'png'
    supported_formats: list = ['png']

    def __init__(self, analysis: Analysis, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the generator.

        Args:
            analysis: Analysis instance to visualize
            config: Optional configuration dict for visualization parameters
        """
        self.analysis = analysis
        self.config = config or {}
        self.file_format = self.config.get('format', self.default_format)

        # Validate format
        if self.file_format not in self.supported_formats:
            raise ValueError(
                f"Unsupported format '{self.file_format}'. "
                f"Supported formats: {', '.join(self.supported_formats)}"
            )

    @abstractmethod
    def generate(self) -> bytes:
        """
        Generate the visualization and return file content as bytes.

        Returns:
            Bytes content of the generated file

        Raises:
            ValueError: If required data is missing or invalid
            RuntimeError: If generation fails
        """
        pass

    @abstractmethod
    def get_title(self) -> str:
        """
        Get the default title for this visualization.

        Returns:
            Title string
        """
        pass

    def get_filename(self) -> str:
        """
        Generate a filename for the visualization.

        Returns:
            Filename string (e.g., 'heatmap_123.png')
        """
        return f"{self.viz_type}_{self.analysis.id}.{self.file_format}"

    def get_file_path(self) -> Path:
        """
        Get the full file path for storing the visualization.

        Returns:
            Path object for the visualization file
        """
        # Create analysis-specific directory
        analysis_dir = Path(settings.MEDIA_ROOT) / 'visualizations' / f'analysis_{self.analysis.id}'
        analysis_dir.mkdir(parents=True, exist_ok=True)

        return analysis_dir / self.get_filename()

    def save_file(self, content: bytes) -> str:
        """
        Save visualization content to file.

        Args:
            content: Bytes content to save

        Returns:
            Relative file path from MEDIA_ROOT
        """
        file_path = self.get_file_path()

        # Write content to file
        with open(file_path, 'wb') as f:
            f.write(content)

        logger.info(f"Saved visualization to {file_path}")

        # Return relative path for storage in database
        return str(file_path.relative_to(settings.MEDIA_ROOT))

    def create_visualization_record(
        self,
        content: bytes,
        user=None,
        title: Optional[str] = None
    ) -> Visualization:
        """
        Create a Visualization model instance and save the file.

        Args:
            content: Visualization file content as bytes
            user: User who created the visualization
            title: Optional custom title (uses get_title() if not provided)

        Returns:
            Created Visualization instance
        """
        # Save file
        file_path = self.save_file(content)

        # Create model instance
        visualization = Visualization.objects.create(
            analysis=self.analysis,
            viz_type=self.viz_type,
            title=title or self.get_title(),
            file_path=file_path,
            file_format=self.file_format,
            file_size=len(content),
            config=self.config,
            created_by=user
        )

        logger.info(f"Created Visualization record: {visualization}")

        return visualization

    def generate_and_save(self, user=None, title: Optional[str] = None) -> Visualization:
        """
        Main entry point: Generate visualization and save it.

        Args:
            user: User creating the visualization
            title: Optional custom title

        Returns:
            Created Visualization instance

        Raises:
            ValueError: If data is invalid
            RuntimeError: If generation fails
        """
        try:
            logger.info(
                f"Generating {self.viz_type} for analysis {self.analysis.id}"
            )

            # Generate content
            content = self.generate()

            # Create record and save file
            visualization = self.create_visualization_record(
                content=content,
                user=user,
                title=title
            )

            logger.info(
                f"Successfully generated {self.viz_type}: "
                f"{visualization.file_size} bytes"
            )

            return visualization

        except Exception as e:
            logger.error(
                f"Failed to generate {self.viz_type} for analysis {self.analysis.id}: {e}",
                exc_info=True
            )
            raise RuntimeError(f"Visualization generation failed: {e}") from e

    def get_data(self) -> Dict[str, Any]:
        """
        Get the data needed for visualization.

        This is a helper method that can be overridden by subclasses
        to provide data in a consistent format.

        Returns:
            Dictionary with visualization data
        """
        from apps.analysis.models import SimilarityResult

        # Get all results for this analysis
        results = SimilarityResult.objects.filter(
            analysis=self.analysis
        ).select_related('text_prompt', 'image')

        # Group by image and prompt
        data = {}
        for result in results:
            image_name = result.image.original_filename
            prompt_text = result.text_prompt.text

            if image_name not in data:
                data[image_name] = {}

            data[image_name][prompt_text] = result.similarity_score

        return data

    def validate_data(self, data: Dict[str, Any]) -> None:
        """
        Validate that we have sufficient data for visualization.

        Args:
            data: Data dictionary to validate

        Raises:
            ValueError: If data is insufficient or invalid
        """
        if not data:
            raise ValueError("No data available for visualization")

        # Check that we have at least one image
        if not any(data.values()):
            raise ValueError("No images with results found")
