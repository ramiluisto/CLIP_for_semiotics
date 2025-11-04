"""
GPS service for extracting and processing GPS data from images.
Adapted from src/gps_utils.py for Django.
"""

from PIL import Image as PILImage
from PIL.ExifTags import TAGS, GPSTAGS
import geopy.distance
from typing import Optional, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class GPSService:
    """
    Service for extracting and processing GPS data from images.
    """

    @staticmethod
    def get_gps_coordinates(image_path: str) -> Optional[Tuple[float, float]]:
        """
        Extract GPS coordinates from an image.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (latitude, longitude) or None if GPS data is not available
        """
        try:
            image = PILImage.open(image_path)
            exif = image._getexif()

            if exif is None:
                return None

            gps_info = {}
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_info[sub_decoded] = value[t]

            if not gps_info:
                return None

            def convert_to_degrees(value):
                """Convert GPS coordinates to degrees."""
                d = float(value[0])
                m = float(value[1])
                s = float(value[2])
                return d + (m / 60.0) + (s / 3600.0)

            gps_latitude = gps_info.get("GPSLatitude")
            gps_latitude_ref = gps_info.get("GPSLatitudeRef")
            gps_longitude = gps_info.get("GPSLongitude")
            gps_longitude_ref = gps_info.get("GPSLongitudeRef")

            if not all([gps_latitude, gps_latitude_ref, gps_longitude, gps_longitude_ref]):
                return None

            lat = convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat = -lat

            lon = convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon = -lon

            return (lat, lon)

        except Exception as e:
            logger.error(f"Error extracting GPS data from {image_path}: {e}")
            return None

    @staticmethod
    def get_altitude(image_path: str) -> Optional[float]:
        """
        Extract altitude from image GPS data.

        Args:
            image_path: Path to the image file

        Returns:
            Altitude in meters or None
        """
        try:
            image = PILImage.open(image_path)
            exif = image._getexif()

            if exif is None:
                return None

            gps_info = {}
            for tag, value in exif.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "GPSInfo":
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_info[sub_decoded] = value[t]

            if not gps_info:
                return None

            gps_altitude = gps_info.get("GPSAltitude")
            if gps_altitude:
                return float(gps_altitude)

            return None

        except Exception as e:
            logger.error(f"Error extracting altitude from {image_path}: {e}")
            return None

    @staticmethod
    def get_closest_location_tag(
        gps_coords: Optional[Tuple[float, float]],
        location_dict: Dict[str, Tuple[float, float]]
    ) -> Optional[str]:
        """
        Find the closest location tag from a dictionary of locations.

        Args:
            gps_coords: Tuple of (latitude, longitude)
            location_dict: Dictionary mapping location names to coordinates

        Returns:
            Name of the closest location or None
        """
        if gps_coords is None or not location_dict:
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
                logger.error(f"Error calculating distance to {place}: {e}")
                continue

        return closest_location

    @staticmethod
    def calculate_distance(
        coords1: Tuple[float, float],
        coords2: Tuple[float, float]
    ) -> float:
        """
        Calculate distance between two GPS coordinates in kilometers.

        Args:
            coords1: First coordinate (lat, lon)
            coords2: Second coordinate (lat, lon)

        Returns:
            Distance in kilometers
        """
        try:
            return geopy.distance.distance(coords1, coords2).km
        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return 0.0

    @staticmethod
    def normalize_coordinates(coordinates_list):
        """
        Normalize a list of GPS coordinates to 0-1 scale.

        Args:
            coordinates_list: List of (latitude, longitude) tuples

        Returns:
            List of (normalized_lat, normalized_lon) tuples
        """
        if not coordinates_list:
            return []

        lats = [coord[0] for coord in coordinates_list]
        lons = [coord[1] for coord in coordinates_list]

        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        lat_range = max_lat - min_lat if max_lat != min_lat else 1.0
        lon_range = max_lon - min_lon if max_lon != min_lon else 1.0

        normalized = []
        for lat, lon in coordinates_list:
            norm_lat = (lat - min_lat) / lat_range
            norm_lon = (lon - min_lon) / lon_range
            normalized.append((norm_lat, norm_lon))

        return normalized


# Create service instance
gps_service = GPSService()
