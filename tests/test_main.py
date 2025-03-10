"""
Tests for the main module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import json
import tempfile

import pandas as pd
from src.main import ClipForHumanists


@patch("src.main.ClipAnalyzer")
def test_init(mock_clip_analyzer):
    """Test initialization of ClipForHumanists."""
    # Initialize ClipForHumanists
    cfh = ClipForHumanists()

    # Check that ClipAnalyzer was initialized
    mock_clip_analyzer.assert_called_once_with("openai/clip-vit-base-patch32")

    # Check that image_data and location_dict were initialized
    assert cfh.image_data == []
    assert cfh.location_dict == {}


def test_set_location_dict():
    """Test set_location_dict method."""
    # Initialize ClipForHumanists with mocked ClipAnalyzer
    with patch("src.main.ClipAnalyzer"):
        cfh = ClipForHumanists()

        # Set location_dict
        location_dict = {
            "New York": (40.7128, -74.0060),
            "Los Angeles": (34.0522, -118.2437),
        }
        cfh.set_location_dict(location_dict)

        # Check that location_dict was set
        assert cfh.location_dict == location_dict


@patch("src.main.extract_gps_from_folder")
def test_process_images(mock_extract_gps):
    """Test process_images method."""
    # Mock extract_gps_from_folder
    mock_extract_gps.return_value = [
        {
            "filepath": "image1.jpg",
            "gps_coordinates": (40.7, -74.0),
            "location_tag": "New York",
        },
        {"filepath": "image2.jpg", "gps_coordinates": None, "location_tag": None},
    ]

    # Mock ClipAnalyzer
    mock_analyzer = MagicMock()
    mock_analyzer.analyze_folder.return_value = [
        {
            "filepath": "image1.jpg",
            "similarities": {"prompt1": 0.8, "prompt2": 0.6},
        },
        {
            "filepath": "image2.jpg",
            "similarities": {"prompt1": 0.7, "prompt2": 0.5},
        },
    ]

    # Initialize ClipForHumanists with mocked ClipAnalyzer
    with patch("src.main.ClipAnalyzer", return_value=mock_analyzer):
        cfh = ClipForHumanists()

        # Process images
        result = cfh.process_images("dummy_folder", ["prompt1", "prompt2"])

        # Check that extract_gps_from_folder was called
        mock_extract_gps.assert_called_once_with("dummy_folder", {})

        # Check that analyze_folder was called
        mock_analyzer.analyze_folder.assert_called_once_with(
            "dummy_folder", ["prompt1", "prompt2"]
        )

        # Check that image_data was set
        assert len(cfh.image_data) == 2
        assert cfh.image_data[0]["filepath"] == "image1.jpg"
        assert cfh.image_data[0]["gps_coordinates"] == (40.7, -74.0)
        assert cfh.image_data[0]["location_tag"] == "New York"
        assert cfh.image_data[0]["similarities"] == {"prompt1": 0.8, "prompt2": 0.6}

        # Check that the result is the same as image_data
        assert result == cfh.image_data


def test_save_and_load_results():
    """Test save_results and load_results methods."""
    # Initialize ClipForHumanists with mocked ClipAnalyzer
    with patch("src.main.ClipAnalyzer"):
        cfh = ClipForHumanists()

        # Set image_data
        cfh.image_data = [
            {
                "filepath": "image1.jpg",
                "gps_coordinates": (40.7, -74.0),
                "location_tag": "New York",
                "similarities": {"prompt1": 0.8, "prompt2": 0.6},
            },
            {
                "filepath": "image2.jpg",
                "gps_coordinates": None,
                "similarities": {"prompt1": 0.7, "prompt2": 0.5},
            },
        ]

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Save results
            cfh.save_results(temp_path)

            # Check that the file exists
            assert os.path.exists(temp_path)

            # Create a new ClipForHumanists instance
            cfh2 = ClipForHumanists()

            # Load results
            cfh2.load_results(temp_path)

            # Check that image_data was loaded
            assert len(cfh2.image_data) == 2
            assert cfh2.image_data[0]["filepath"] == "image1.jpg"
            assert cfh2.image_data[0]["gps_coordinates"] == [40.7, -74.0]
            assert cfh2.image_data[0]["location_tag"] == "New York"
            assert cfh2.image_data[0]["similarities"] == {
                "prompt1": 0.8,
                "prompt2": 0.6,
            }

        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.remove(temp_path)


def test_get_dataframe():
    """Test get_dataframe method."""
    # Initialize ClipForHumanists with mocked ClipAnalyzer
    with patch("src.main.ClipAnalyzer"):
        cfh = ClipForHumanists()

        # Set image_data
        cfh.image_data = [
            {
                "filepath": "path/to/image1.jpg",
                "gps_coordinates": (40.7, -74.0),
                "location_tag": "New York",
                "similarities": {"prompt1": 0.8, "prompt2": 0.6},
            },
            {
                "filepath": "path/to/image2.jpg",
                "gps_coordinates": None,
                "similarities": {"prompt1": 0.7, "prompt2": 0.5},
            },
        ]

        # Get dataframe
        df = cfh.get_dataframe()

        # Check that the dataframe has the expected structure
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert df.iloc[0]["filepath"] == "path/to/image1.jpg"
        assert df.iloc[0]["filename"] == "image1.jpg"
        assert df.iloc[0]["latitude"] == 40.7
        assert df.iloc[0]["longitude"] == -74.0
        assert df.iloc[0]["location_tag"] == "New York"
        assert df.iloc[0]["similarity_prompt1"] == 0.8
        assert df.iloc[0]["similarity_prompt2"] == 0.6

        # Check that the second row has None for latitude and longitude
        assert pd.isna(df.iloc[1].get("latitude", None))
        assert pd.isna(df.iloc[1].get("longitude", None))

        # Test with empty image_data
        cfh.image_data = []
        with pytest.raises(ValueError):
            cfh.get_dataframe()


def test_get_top_images_for_prompt():
    """Test get_top_images_for_prompt method."""
    # Initialize ClipForHumanists with mocked ClipAnalyzer
    with patch("src.main.ClipAnalyzer"):
        cfh = ClipForHumanists()

        # Set image_data
        cfh.image_data = [
            {
                "filepath": "image1.jpg",
                "similarities": {"prompt1": 0.8, "prompt2": 0.6},
            },
            {
                "filepath": "image2.jpg",
                "similarities": {"prompt1": 0.9, "prompt2": 0.5},
            },
            {
                "filepath": "image3.jpg",
                "similarities": {"prompt1": 0.7, "prompt2": 0.7},
            },
        ]

        # Get top images for prompt1
        top_images = cfh.get_top_images_for_prompt("prompt1", 2)

        # Check that we got 2 results
        assert len(top_images) == 2

        # Check that the results are sorted by score in descending order
        assert top_images[0]["filepath"] == "image2.jpg"
        assert top_images[0]["score"] == 0.9
        assert top_images[1]["filepath"] == "image1.jpg"
        assert top_images[1]["score"] == 0.8

        # Get top images for prompt2
        top_images = cfh.get_top_images_for_prompt("prompt2", 1)

        # Check that we got 1 result
        assert len(top_images) == 1

        # Check that the result is the image with the highest score for prompt2
        assert top_images[0]["filepath"] == "image3.jpg"
        assert top_images[0]["score"] == 0.7

        # Test with empty image_data
        cfh.image_data = []
        with pytest.raises(ValueError):
            cfh.get_top_images_for_prompt("prompt1")
