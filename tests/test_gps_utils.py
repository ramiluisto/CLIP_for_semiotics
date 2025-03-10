"""
Tests for the GPS utilities.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from src.gps_utils import (
    get_gps_coordinates,
    get_closest_location_tag,
    extract_gps_from_folder,
)


def test_get_closest_location_tag():
    """Test get_closest_location_tag function."""
    # Test with valid coordinates
    location_dict = {
        "New York": (40.7128, -74.0060),
        "Los Angeles": (34.0522, -118.2437),
    }

    # Test with coordinates close to New York
    coords = (40.7, -74.0)
    result = get_closest_location_tag(coords, location_dict)
    assert result == "New York"

    # Test with coordinates close to Los Angeles
    coords = (34.1, -118.3)
    result = get_closest_location_tag(coords, location_dict)
    assert result == "Los Angeles"

    # Test with None coordinates
    result = get_closest_location_tag(None, location_dict)
    assert result is None


@patch("src.gps_utils.Image")
def test_get_gps_coordinates_no_exif(mock_image):
    """Test get_gps_coordinates function with no EXIF data."""
    # Mock Image.open and _getexif
    mock_img = MagicMock()
    mock_img._getexif.return_value = None
    mock_image.open.return_value = mock_img

    result = get_gps_coordinates("dummy_path.jpg")
    assert result is None


@patch("src.gps_utils.Image")
def test_get_gps_coordinates_no_gps_info(mock_image):
    """Test get_gps_coordinates function with no GPS info."""
    # Mock Image.open and _getexif
    mock_img = MagicMock()
    mock_img._getexif.return_value = {1: "test"}  # No GPS info
    mock_image.open.return_value = mock_img

    result = get_gps_coordinates("dummy_path.jpg")
    assert result is None


@patch("src.gps_utils.os.path.exists")
@patch("src.gps_utils.os.listdir")
@patch("src.gps_utils.get_gps_coordinates")
def test_extract_gps_from_folder(mock_get_gps, mock_listdir, mock_exists):
    """Test extract_gps_from_folder function."""
    # Mock os.path.exists
    mock_exists.return_value = True

    # Mock os.listdir
    mock_listdir.return_value = ["image1.jpg", "image2.jpg", "file.txt"]

    # Mock get_gps_coordinates
    mock_get_gps.side_effect = [(40.7, -74.0), None]

    # Test with no location_dict
    result = extract_gps_from_folder("dummy_folder")

    # Check that we got 2 results (for the 2 jpg files)
    assert len(result) == 2

    # Check that the first result has GPS coordinates
    assert result[0]["gps_coordinates"] == (40.7, -74.0)

    # Check that the second result has None for GPS coordinates
    assert result[1]["gps_coordinates"] is None

    # Test with location_dict
    location_dict = {
        "New York": (40.7128, -74.0060),
        "Los Angeles": (34.0522, -118.2437),
    }

    # Reset mock_get_gps
    mock_get_gps.reset_mock()
    mock_get_gps.side_effect = [(40.7, -74.0), None]

    result = extract_gps_from_folder("dummy_folder", location_dict)

    # Check that we got 2 results
    assert len(result) == 2

    # Check that the first result has a location_tag
    assert result[0]["location_tag"] == "New York"

    # Check that the second result has None for location_tag
    assert result[1]["location_tag"] is None

    # Test with non-existent folder
    mock_exists.return_value = False
    with pytest.raises(ValueError):
        extract_gps_from_folder("non_existent_folder")
