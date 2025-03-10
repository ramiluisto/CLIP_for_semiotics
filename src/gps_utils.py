"""
Utilities for extracting and processing GPS data from images.
"""

import os
from typing import Dict, List, Optional, Tuple, Union

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import geopy.distance


def get_gps_coordinates(img_path: str) -> Optional[Tuple[float, float]]:
    """
    Extract GPS coordinates from an image.

    Args:
        img_path: Path to the image file

    Returns:
        Tuple of (latitude, longitude) or None if GPS data is not available
    """
    try:
        image = Image.open(img_path)
        info = image._getexif()
        if info is None:
            return None

        gps_info = {}
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_info[sub_decoded] = value[t]

        if not gps_info:
            return None

        def get_if_exist(data, key):
            return data.get(key)

        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)

        lat = None
        lon = None

        gps_latitude = get_if_exist(gps_info, "GPSLatitude")
        gps_latitude_ref = get_if_exist(gps_info, "GPSLatitudeRef")
        gps_longitude = get_if_exist(gps_info, "GPSLongitude")
        gps_longitude_ref = get_if_exist(gps_info, "GPSLongitudeRef")

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat = 0 - lat

            lon = convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon = 0 - lon

        return (lat, lon)
    except Exception as e:
        print(f"Error extracting GPS data from {img_path}: {e}")
        return None


def get_closest_location_tag(
    gps_coords: Optional[Tuple[float, float]],
    location_dict: Dict[str, Tuple[float, float]],
) -> Optional[str]:
    """
    Find the closest location tag from a dictionary of locations.

    Args:
        gps_coords: Tuple of (latitude, longitude)
        location_dict: Dictionary mapping location names to (lat, lon) coordinates

    Returns:
        Name of the closest location or None if GPS coordinates are not available
    """
    if gps_coords is None:
        return None

    closest_location = None
    min_distance = float("inf")

    for place, coords in location_dict.items():
        try:
            distance = geopy.distance.distance(gps_coords, coords).km
            if distance < min_distance:
                min_distance = distance
                closest_location = place
        except Exception as e:
            print(f"Error calculating distance to {place}: {e}")
            continue

    return closest_location


def extract_gps_from_folder(
    folder_path: str, location_dict: Optional[Dict[str, Tuple[float, float]]] = None
) -> List[Dict[str, Union[str, Tuple[float, float], Optional[str]]]]:
    """
    Extract GPS coordinates from all images in a folder.

    Args:
        folder_path: Path to the folder containing images
        location_dict: Optional dictionary mapping location names to coordinates

    Returns:
        List of dictionaries with filepath, gps_coordinates, and location_tag
    """
    if not os.path.exists(folder_path):
        raise ValueError(f"Folder path does not exist: {folder_path}")

    # List all jpg files in the folder
    jpg_files = [
        f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg"))
    ]

    # Create a list of dictionaries
    data = []
    for jpg_file in jpg_files:
        file_path = os.path.join(folder_path, jpg_file)
        gps_coords = get_gps_coordinates(file_path)

        result = {
            "filepath": file_path,
            "gps_coordinates": gps_coords,
        }

        if location_dict is not None:
            location_tag = get_closest_location_tag(gps_coords, location_dict)
            result["location_tag"] = location_tag

        data.append(result)

    return data
