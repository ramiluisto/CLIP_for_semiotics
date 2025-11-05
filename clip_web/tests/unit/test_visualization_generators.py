"""
Unit tests for visualization generators.
"""

import pytest
from io import BytesIO
from PIL import Image as PILImage
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from apps.visualizations.generators import (
    BaseGenerator,
    HeatmapGenerator,
    CorrelationMatrixGenerator,
    ImageGridGenerator
)
from apps.visualizations.models import Visualization
from apps.analysis.models import Analysis, SimilarityResult


@pytest.mark.django_db
class TestBaseGenerator:
    """Tests for BaseGenerator abstract class."""

    def test_cannot_instantiate_directly(self, analysis):
        """BaseGenerator is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseGenerator(analysis)

    def test_get_file_path(self, analysis):
        """Test file path generation."""
        generator = HeatmapGenerator(analysis)
        path = generator.get_file_path()

        assert 'visualizations' in str(path)
        assert f'analysis_{analysis.id}' in str(path)
        assert 'heatmap' in str(path)
        assert path.suffix == '.png'

    def test_get_file_path_with_custom_format(self, analysis):
        """Test file path with custom format."""
        generator = HeatmapGenerator(analysis, config={'format': 'svg'})
        path = generator.get_file_path()

        assert path.suffix == '.svg'

    def test_get_data_retrieves_similarity_results(self, analysis, similarity_results):
        """Test that get_data retrieves similarity results correctly."""
        generator = HeatmapGenerator(analysis)
        data = generator.get_data()

        assert isinstance(data, dict)
        assert len(data) > 0
        # Data should be image_name -> {prompt: score}
        for img_data in data.values():
            assert isinstance(img_data, dict)

    def test_validate_data_empty(self, analysis):
        """Test validation fails on empty data."""
        generator = HeatmapGenerator(analysis)

        with pytest.raises(ValueError, match="No data available"):
            generator.validate_data({})

    def test_config_defaults(self, analysis):
        """Test default configuration."""
        generator = HeatmapGenerator(analysis)

        assert generator.config == {}
        assert generator.viz_type == 'heatmap'
        assert generator.file_format == 'png'

    def test_config_custom(self, analysis):
        """Test custom configuration."""
        config = {
            'colormap': 'plasma',
            'dpi': 150,
            'format': 'svg'
        }
        generator = HeatmapGenerator(analysis, config=config)

        assert generator.config == config
        assert generator.file_format == 'svg'


@pytest.mark.django_db
class TestHeatmapGenerator:
    """Tests for HeatmapGenerator."""

    def test_init(self, analysis):
        """Test initialization."""
        generator = HeatmapGenerator(analysis)

        assert generator.analysis == analysis
        assert generator.viz_type == 'heatmap'
        assert generator.default_format == 'png'
        assert 'png' in generator.supported_formats

    def test_get_title(self, analysis):
        """Test title generation."""
        generator = HeatmapGenerator(analysis)
        title = generator.get_title()

        assert analysis.name in title
        assert 'Heatmap' in title or 'heatmap' in title.lower()

    @patch('apps.visualizations.generators.heatmaps.plt')
    def test_generate_creates_figure(self, mock_plt, analysis, similarity_results):
        """Test that generate creates a matplotlib figure."""
        generator = HeatmapGenerator(analysis)

        # Mock the figure and axes
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        # Mock savefig to return bytes
        def mock_savefig(buffer, **kwargs):
            buffer.write(b'fake image data')
        mock_fig.savefig = mock_savefig

        result = generator.generate()

        assert isinstance(result, bytes)
        assert len(result) > 0
        mock_plt.subplots.assert_called_once()
        mock_ax.imshow.assert_called_once()

    def test_generate_with_config(self, analysis, similarity_results):
        """Test generation with custom configuration."""
        config = {
            'colormap': 'coolwarm',
            'dpi': 150,
            'show_values': True
        }
        generator = HeatmapGenerator(analysis, config=config)

        # This would actually generate the visualization
        # We'll just test that it accepts the config
        assert generator.config['colormap'] == 'coolwarm'
        assert generator.config['dpi'] == 150
        assert generator.config['show_values'] is True

    def test_validate_data_minimum_requirements(self, analysis):
        """Test validation for minimum data requirements."""
        generator = HeatmapGenerator(analysis)

        # Empty data
        with pytest.raises(ValueError):
            generator.validate_data({})

        # Valid minimal data
        data = {
            'image1.jpg': {'prompt1': 0.5, 'prompt2': 0.7}
        }
        # Should not raise
        generator.validate_data(data)

    def test_supported_formats(self, analysis):
        """Test that generator supports multiple formats."""
        generator = HeatmapGenerator(analysis)

        assert 'png' in generator.supported_formats
        assert 'svg' in generator.supported_formats
        assert 'pdf' in generator.supported_formats


@pytest.mark.django_db
class TestCorrelationMatrixGenerator:
    """Tests for CorrelationMatrixGenerator."""

    def test_init(self, analysis):
        """Test initialization."""
        generator = CorrelationMatrixGenerator(analysis)

        assert generator.analysis == analysis
        assert generator.viz_type == 'correlation'
        assert generator.default_format == 'png'

    def test_get_title(self, analysis):
        """Test title generation."""
        generator = CorrelationMatrixGenerator(analysis)
        title = generator.get_title()

        assert analysis.name in title
        assert 'Correlation' in title

    def test_validate_data_minimum_prompts(self, analysis):
        """Test validation requires at least 2 prompts."""
        generator = CorrelationMatrixGenerator(analysis)

        # Only 1 prompt - should fail
        data = {
            'image1.jpg': {'prompt1': 0.5},
            'image2.jpg': {'prompt1': 0.7}
        }
        with pytest.raises(ValueError, match="at least 2 text prompts"):
            generator.validate_data(data)

        # 2 prompts - should pass
        data = {
            'image1.jpg': {'prompt1': 0.5, 'prompt2': 0.6},
            'image2.jpg': {'prompt1': 0.7, 'prompt2': 0.8}
        }
        generator.validate_data(data)

    def test_validate_data_minimum_images(self, analysis):
        """Test validation requires at least 2 images."""
        generator = CorrelationMatrixGenerator(analysis)

        # Only 1 image - should fail
        data = {
            'image1.jpg': {'prompt1': 0.5, 'prompt2': 0.6}
        }
        with pytest.raises(ValueError, match="at least 2 images"):
            generator.validate_data(data)

        # 2 images - should pass
        data = {
            'image1.jpg': {'prompt1': 0.5, 'prompt2': 0.6},
            'image2.jpg': {'prompt1': 0.7, 'prompt2': 0.8}
        }
        generator.validate_data(data)

    def test_validate_data_consistent_prompts(self, analysis):
        """Test validation requires consistent prompts across images."""
        generator = CorrelationMatrixGenerator(analysis)

        # Inconsistent prompts - should fail
        data = {
            'image1.jpg': {'prompt1': 0.5, 'prompt2': 0.6},
            'image2.jpg': {'prompt1': 0.7, 'prompt3': 0.8}  # Different prompt!
        }
        with pytest.raises(ValueError, match="different prompts"):
            generator.validate_data(data)

    @pytest.mark.skip(reason="Mock issue with numpy array comparison - needs refactoring")
    @patch('apps.visualizations.generators.correlations.plt')
    @patch('apps.visualizations.generators.correlations.pd')
    def test_generate_calculates_correlations(self, mock_pd, mock_plt, analysis, similarity_results):
        """Test that generate calculates correlations."""
        generator = CorrelationMatrixGenerator(analysis)

        # Mock pandas DataFrame and correlation calculation
        mock_df = MagicMock()
        mock_corr = MagicMock()
        mock_df.corr.return_value = mock_corr
        mock_pd.DataFrame.return_value = mock_df

        # Mock matplotlib
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)

        def mock_savefig(buffer, **kwargs):
            buffer.write(b'correlation matrix')
        mock_fig.savefig = mock_savefig

        result = generator.generate()

        assert isinstance(result, bytes)
        mock_pd.DataFrame.assert_called_once()
        mock_df.corr.assert_called_once()


@pytest.mark.django_db
class TestImageGridGenerator:
    """Tests for ImageGridGenerator."""

    def test_init(self, analysis):
        """Test initialization."""
        generator = ImageGridGenerator(analysis)

        assert generator.analysis == analysis
        assert generator.viz_type == 'image_grid'
        assert generator.default_format == 'png'

    def test_get_title(self, analysis):
        """Test title generation."""
        generator = ImageGridGenerator(analysis)
        title = generator.get_title()

        assert analysis.name in title
        assert 'Grid' in title or 'grid' in title.lower()

    def test_get_title_with_prompt(self, analysis):
        """Test title generation with specific prompt."""
        config = {'prompt': 'architecture'}
        generator = ImageGridGenerator(analysis, config=config)
        title = generator.get_title()

        assert 'architecture' in title

    def test_validate_data_no_images(self, analysis):
        """Test validation fails with no images."""
        generator = ImageGridGenerator(analysis)

        with pytest.raises(ValueError, match="No data available"):
            generator.validate_data({})

    def test_validate_data_no_scores(self, analysis):
        """Test validation fails when images have no scores."""
        generator = ImageGridGenerator(analysis)

        data = {'image1.jpg': {}}
        with pytest.raises(ValueError, match="No images with results"):
            generator.validate_data(data)

    def test_validate_data_prompt_not_found(self, analysis):
        """Test validation when specific prompt not found."""
        config = {'prompt': 'nonexistent'}
        generator = ImageGridGenerator(analysis, config=config)

        data = {
            'image1.jpg': {'prompt1': 0.5, 'prompt2': 0.7}
        }
        with pytest.raises(ValueError, match="not found"):
            generator.validate_data(data)

    def test_config_defaults(self, analysis):
        """Test default configuration values."""
        generator = ImageGridGenerator(analysis)

        # These are applied during generation, not init
        # Just verify the generator accepts them
        config = generator.config
        assert isinstance(config, dict)

    def test_config_custom_grid_layout(self, analysis):
        """Test custom grid configuration."""
        config = {
            'cols': 4,
            'max_images': 20,
            'sort_by': 'name',
            'sort_order': 'asc'
        }
        generator = ImageGridGenerator(analysis, config=config)

        assert generator.config['cols'] == 4
        assert generator.config['max_images'] == 20
        assert generator.config['sort_by'] == 'name'
        assert generator.config['sort_order'] == 'asc'


@pytest.mark.django_db
class TestVisualizationIntegration:
    """Integration tests for visualization generation workflow."""

    def test_generate_and_save_creates_visualization(self, user, analysis, similarity_results):
        """Test that generate_and_save creates a Visualization object."""
        generator = HeatmapGenerator(analysis)

        with patch.object(generator, 'generate', return_value=b'fake image'):
            visualization = generator.generate_and_save(user=user)

        assert isinstance(visualization, Visualization)
        assert visualization.analysis == analysis
        assert visualization.viz_type == 'heatmap'
        assert visualization.created_by == user
        assert visualization.file_format == 'png'

    def test_generate_and_save_with_custom_title(self, user, analysis, similarity_results):
        """Test custom title in generate_and_save."""
        generator = HeatmapGenerator(analysis)
        custom_title = "My Custom Heatmap"

        with patch.object(generator, 'generate', return_value=b'fake image'):
            visualization = generator.generate_and_save(user=user, title=custom_title)

        assert visualization.title == custom_title

    def test_save_file_creates_file(self, analysis, similarity_results):
        """Test that save_file creates a file."""
        generator = HeatmapGenerator(analysis)
        content = b'test image content'

        file_path = generator.save_file(content)

        assert file_path is not None
        assert 'heatmap' in file_path
        assert file_path.endswith('.png')

    def test_multiple_generators_same_analysis(self, user, analysis, similarity_results):
        """Test generating multiple visualization types for same analysis."""
        generators = [
            HeatmapGenerator(analysis),
            CorrelationMatrixGenerator(analysis),
        ]

        visualizations = []
        for generator in generators:
            with patch.object(generator, 'generate', return_value=b'fake image'):
                viz = generator.generate_and_save(user=user)
                visualizations.append(viz)

        assert len(visualizations) == 2
        assert visualizations[0].viz_type == 'heatmap'
        assert visualizations[1].viz_type == 'correlation'
        assert all(v.analysis == analysis for v in visualizations)


@pytest.mark.django_db
class TestErrorHandling:
    """Test error handling in generators."""

    def test_generate_with_no_data(self, analysis):
        """Test generation fails gracefully with no data."""
        generator = HeatmapGenerator(analysis)

        # Mock get_data to return empty
        with patch.object(generator, 'get_data', return_value={}):
            with pytest.raises(ValueError):
                generator.generate()

    def test_generate_with_invalid_config(self, analysis, similarity_results):
        """Test that invalid config values are handled."""
        # Invalid colormap should be handled by matplotlib
        config = {'colormap': 'nonexistent_colormap'}
        generator = HeatmapGenerator(analysis, config=config)

        # This would typically raise or fall back to default
        # Specific behavior depends on implementation

    def test_file_save_error_handling(self, analysis):
        """Test error handling when file save fails."""
        generator = HeatmapGenerator(analysis)

        # This would test scenarios like disk full, permission denied, etc.
        # For now, just verify the method exists
        assert hasattr(generator, 'save_file')
