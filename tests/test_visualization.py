"""
Tests for the visualization module.
"""

import pytest
from unittest.mock import patch, MagicMock

import numpy as np
import matplotlib.pyplot as plt
import folium
from PIL import Image

from src.visualization import (
    plot_similarity_heatmap,
    create_map_with_images,
    plot_similarity_by_location,
    display_image_grid,
)


@patch("src.visualization.plt.subplots")
def test_plot_similarity_heatmap(mock_subplots):
    """Test plot_similarity_heatmap function."""
    # Mock plt.subplots
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_subplots.return_value = (mock_fig, mock_ax)

    # Mock imshow
    mock_im = MagicMock()
    mock_ax.imshow.return_value = mock_im

    # Mock colorbar
    mock_cbar = MagicMock()
    mock_fig.colorbar.return_value = mock_cbar

    # Create test data
    similarities = {
        "image1.jpg": {"prompt1": 0.8, "prompt2": 0.6},
        "image2.jpg": {"prompt1": 0.7, "prompt2": 0.5},
    }

    # Call the function
    result = plot_similarity_heatmap(similarities, "Test Heatmap")

    # Check that plt.subplots was called
    mock_subplots.assert_called_once()

    # Check that ax.imshow was called with a 2x2 matrix
    mock_ax.imshow.assert_called_once()
    args, kwargs = mock_ax.imshow.call_args
    assert args[0].shape == (2, 2)  # 2 images, 2 prompts

    # Check that ax.set_title was called with the title
    mock_ax.set_title.assert_called_once_with("Test Heatmap")

    # Check that the result is the mock figure
    assert result == mock_fig

    # Test with empty similarities
    with pytest.raises(ValueError):
        plot_similarity_heatmap({})


@patch("src.visualization.folium.Map")
@patch("src.visualization.folium.Marker")
@patch("src.visualization.Image")
def test_create_map_with_images(mock_image, mock_marker, mock_map):
    """Test create_map_with_images function."""
    # Mock folium.Map
    mock_map_instance = MagicMock()
    mock_map.return_value = mock_map_instance

    # Mock folium.Marker
    mock_marker_instance = MagicMock()
    mock_marker.return_value = mock_marker_instance

    # Mock PIL.Image
    mock_img = MagicMock()
    mock_image.open.return_value = mock_img

    # Create test data
    image_data = [
        {"filepath": "image1.jpg", "gps_coordinates": (40.7, -74.0)},
        {"filepath": "image2.jpg", "gps_coordinates": (34.0, -118.2)},
    ]

    # Call the function
    result = create_map_with_images(image_data)

    # Check that folium.Map was called
    mock_map.assert_called_once()

    # Check that folium.Marker was called twice (once for each image)
    assert mock_marker.call_count == 2

    # Check that the result is the mock map
    assert result == mock_map_instance

    # Test with no valid images
    with pytest.raises(ValueError):
        create_map_with_images([{"filepath": "image1.jpg", "gps_coordinates": None}])


@patch("src.visualization.plt.subplots")
def test_plot_similarity_by_location(mock_subplots):
    """Test plot_similarity_by_location function."""
    # Mock plt.subplots
    mock_fig = MagicMock()
    mock_ax = MagicMock()
    mock_subplots.return_value = (mock_fig, mock_ax)

    # Create test data
    image_data = [
        {
            "filepath": "image1.jpg",
            "location_tag": "New York",
            "similarities": {"prompt1": 0.8, "prompt2": 0.6},
        },
        {
            "filepath": "image2.jpg",
            "location_tag": "New York",
            "similarities": {"prompt1": 0.7, "prompt2": 0.5},
        },
        {
            "filepath": "image3.jpg",
            "location_tag": "Los Angeles",
            "similarities": {"prompt1": 0.6, "prompt2": 0.7},
        },
    ]

    # Call the function
    result = plot_similarity_by_location(image_data, "prompt1")

    # Check that plt.subplots was called
    mock_subplots.assert_called_once()

    # Check that ax.boxplot was called
    mock_ax.boxplot.assert_called_once()

    # Check that ax.set_title was called
    mock_ax.set_title.assert_called_once()

    # Check that the result is the mock figure
    assert result == mock_fig

    # Test with no valid images
    with pytest.raises(ValueError):
        plot_similarity_by_location(
            [{"filepath": "image1.jpg", "similarities": {"prompt1": 0.8}}],
            "prompt1",
        )


@patch("src.visualization.plt.figure")
@patch("src.visualization.Image")
def test_display_image_grid(mock_image, mock_figure):
    """Test display_image_grid function."""
    # Mock plt.figure
    mock_fig = MagicMock()
    mock_figure.return_value = mock_fig

    # Mock fig.add_subplot
    mock_subplot = MagicMock()
    mock_fig.add_subplot.return_value = mock_subplot

    # Mock PIL.Image
    mock_img = MagicMock()
    mock_image.open.return_value = mock_img

    # Create test data
    image_paths = ["image1.jpg", "image2.jpg"]
    similarities = {
        "image1.jpg": {"prompt1": 0.8, "prompt2": 0.6},
        "image2.jpg": {"prompt1": 0.7, "prompt2": 0.5},
    }

    # Call the function
    result = display_image_grid(image_paths, similarities, "prompt1")

    # Check that plt.figure was called
    mock_figure.assert_called_once()

    # Check that fig.add_subplot was called twice (once for each image)
    assert mock_fig.add_subplot.call_count == 2

    # Check that the result is the mock figure
    assert result == mock_fig
