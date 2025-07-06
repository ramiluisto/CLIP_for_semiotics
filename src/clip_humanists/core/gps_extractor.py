"""Enhanced GPS extraction with improved error handling and metadata."""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import geopy.distance
import numpy as np

from .config import get_config


logger = logging.getLogger(__name__)


@dataclass
class GPSResult:
    """Result from GPS extraction."""
    filepath: str
    gps_coordinates: Optional[Tuple[float, float]] = None
    location_tag: Optional[str] = None
    timestamp: Optional[datetime] = None
    altitude: Optional[float] = None
    heading: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class GPSExtractor:
    """
    Enhanced GPS extractor with improved error handling and metadata extraction.
    """
    
    def __init__(
        self,
        location_dict: Optional[Dict[str, Tuple[float, float]]] = None,
        max_distance_km: float = 10.0,
    ):
        """
        Initialize GPS extractor.
        
        Args:
            location_dict: Dictionary mapping location names to (lat, lon) coordinates
            max_distance_km: Maximum distance in km to consider for location matching
        """
        self.config = get_config()
        self.location_dict = location_dict or {}
        self.max_distance_km = max_distance_km
        
        # Statistics
        self.stats = {
            "images_processed": 0,
            "gps_found": 0,
            "locations_matched": 0,
            "errors": 0,
        }
    
    def _convert_to_degrees(self, value: Tuple[float, float, float]) -> float:
        """Convert GPS coordinates from DMS to decimal degrees."""
        try:
            degrees = float(value[0])
            minutes = float(value[1])
            seconds = float(value[2])
            return degrees + (minutes / 60.0) + (seconds / 3600.0)
        except (IndexError, ValueError, TypeError) as e:
            logger.warning(f"Error converting GPS coordinates: {e}")
            return 0.0
    
    def _extract_timestamp(self, exif_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract timestamp from EXIF data."""
        try:
            # Try different timestamp fields
            timestamp_fields = [
                'DateTime',
                'DateTimeOriginal', 
                'DateTimeDigitized',
                'GPS GPSTimeStamp',
                'GPS GPSDateStamp'
            ]
            
            for field in timestamp_fields:
                if field in exif_data:
                    timestamp_str = exif_data[field]
                    if isinstance(timestamp_str, str):
                        # Try to parse different formats
                        try:
                            return datetime.strptime(timestamp_str, "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            try:
                                return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting timestamp: {e}")
            return None
    
    def _extract_altitude(self, gps_info: Dict[str, Any]) -> Optional[float]:
        """Extract altitude from GPS info."""
        try:
            if 'GPSAltitude' in gps_info:
                altitude = float(gps_info['GPSAltitude'])
                
                # Check altitude reference (0 = above sea level, 1 = below sea level)
                if 'GPSAltitudeRef' in gps_info and gps_info['GPSAltitudeRef'] == 1:
                    altitude = -altitude
                
                return altitude
                
        except Exception as e:
            logger.debug(f"Error extracting altitude: {e}")
            
        return None
    
    def _extract_heading(self, gps_info: Dict[str, Any]) -> Optional[float]:
        """Extract heading/direction from GPS info."""
        try:
            if 'GPSImgDirection' in gps_info:
                return float(gps_info['GPSImgDirection'])
            elif 'GPSTrack' in gps_info:
                return float(gps_info['GPSTrack'])
        except Exception as e:
            logger.debug(f"Error extracting heading: {e}")
            
        return None
    
    def extract_gps_data(self, image_path: str) -> GPSResult:
        """
        Extract GPS data from a single image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            GPSResult object with extracted data
        """
        self.stats["images_processed"] += 1
        
        try:
            # Open image and get EXIF data
            with Image.open(image_path) as image:
                exif_data = image._getexif()
                
            if exif_data is None:
                return GPSResult(filepath=image_path)
            
            # Convert EXIF data to readable format
            exif_dict = {}
            gps_info = {}
            
            for tag, value in exif_data.items():
                decoded = TAGS.get(tag, tag)
                exif_dict[decoded] = value
                
                if decoded == "GPSInfo":
                    for t in value:
                        sub_decoded = GPSTAGS.get(t, t)
                        gps_info[sub_decoded] = value[t]
            
            # Extract timestamp
            timestamp = self._extract_timestamp(exif_dict)
            
            # Extract GPS coordinates
            gps_coordinates = None
            if gps_info:
                lat = None
                lon = None
                
                # Extract latitude
                if 'GPSLatitude' in gps_info and 'GPSLatitudeRef' in gps_info:
                    lat = self._convert_to_degrees(gps_info['GPSLatitude'])
                    if gps_info['GPSLatitudeRef'] != 'N':
                        lat = -lat
                
                # Extract longitude
                if 'GPSLongitude' in gps_info and 'GPSLongitudeRef' in gps_info:
                    lon = self._convert_to_degrees(gps_info['GPSLongitude'])
                    if gps_info['GPSLongitudeRef'] != 'E':
                        lon = -lon
                
                if lat is not None and lon is not None:
                    gps_coordinates = (lat, lon)
                    self.stats["gps_found"] += 1
            
            # Extract additional GPS metadata
            altitude = self._extract_altitude(gps_info)
            heading = self._extract_heading(gps_info)
            
            # Find closest location
            location_tag = None
            if gps_coordinates and self.location_dict:
                location_tag = self._find_closest_location(gps_coordinates)
                if location_tag:
                    self.stats["locations_matched"] += 1
            
            # Create metadata dictionary
            metadata = {
                "camera_make": exif_dict.get("Make"),
                "camera_model": exif_dict.get("Model"),
                "image_width": exif_dict.get("ExifImageWidth"),
                "image_height": exif_dict.get("ExifImageHeight"),
                "orientation": exif_dict.get("Orientation"),
                "gps_processing_method": gps_info.get("GPSProcessingMethod"),
                "gps_satellites": gps_info.get("GPSSatellites"),
                "gps_measure_mode": gps_info.get("GPSMeasureMode"),
                "gps_dop": gps_info.get("GPSDOP"),  # Dilution of Precision
            }
            
            # Remove None values
            metadata = {k: v for k, v in metadata.items() if v is not None}
            
            return GPSResult(
                filepath=image_path,
                gps_coordinates=gps_coordinates,
                location_tag=location_tag,
                timestamp=timestamp,
                altitude=altitude,
                heading=heading,
                metadata=metadata,
            )
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            self.stats["errors"] += 1
            return GPSResult(filepath=image_path)
    
    def _find_closest_location(
        self, 
        gps_coords: Tuple[float, float]
    ) -> Optional[str]:
        """
        Find the closest location from the location dictionary.
        
        Args:
            gps_coords: GPS coordinates as (lat, lon)
            
        Returns:
            Name of the closest location or None
        """
        if not self.location_dict:
            return None
        
        min_distance = float('inf')
        closest_location = None
        
        for location_name, location_coords in self.location_dict.items():
            try:
                distance = geopy.distance.distance(gps_coords, location_coords).km
                if distance < min_distance and distance <= self.max_distance_km:
                    min_distance = distance
                    closest_location = location_name
            except Exception as e:
                logger.debug(f"Error calculating distance to {location_name}: {e}")
                continue
        
        return closest_location
    
    def extract_batch(
        self, 
        image_paths: List[str],
        show_progress: bool = True
    ) -> List[GPSResult]:
        """
        Extract GPS data from multiple images.
        
        Args:
            image_paths: List of paths to image files
            show_progress: Whether to show progress bar
            
        Returns:
            List of GPSResult objects
        """
        results = []
        
        # Import tqdm only if needed
        if show_progress:
            from tqdm import tqdm
            iterator = tqdm(image_paths, desc="Extracting GPS data")
        else:
            iterator = image_paths
        
        for image_path in iterator:
            result = self.extract_gps_data(image_path)
            results.append(result)
        
        return results
    
    def extract_from_folder(
        self, 
        folder_path: str,
        recursive: bool = False,
        show_progress: bool = True
    ) -> List[GPSResult]:
        """
        Extract GPS data from all images in a folder.
        
        Args:
            folder_path: Path to folder containing images
            recursive: Whether to search recursively in subfolders
            show_progress: Whether to show progress bar
            
        Returns:
            List of GPSResult objects
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        # Find all image files
        image_paths = []
        valid_formats = self.config.processing.supported_formats
        
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(fmt) for fmt in valid_formats):
                        image_paths.append(os.path.join(root, file))
        else:
            for file in os.listdir(folder_path):
                if any(file.lower().endswith(fmt) for fmt in valid_formats):
                    image_paths.append(os.path.join(folder_path, file))
        
        logger.info(f"Found {len(image_paths)} images in {folder_path}")
        
        return self.extract_batch(image_paths, show_progress)
    
    def set_location_dict(self, location_dict: Dict[str, Tuple[float, float]]) -> None:
        """
        Set the location dictionary for location matching.
        
        Args:
            location_dict: Dictionary mapping location names to (lat, lon) coordinates
        """
        self.location_dict = location_dict
        logger.info(f"Updated location dictionary with {len(location_dict)} locations")
    
    def add_location(self, name: str, coordinates: Tuple[float, float]) -> None:
        """
        Add a single location to the location dictionary.
        
        Args:
            name: Name of the location
            coordinates: GPS coordinates as (lat, lon)
        """
        self.location_dict[name] = coordinates
        logger.info(f"Added location: {name} at {coordinates}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        stats = self.stats.copy()
        
        if stats["images_processed"] > 0:
            stats["gps_success_rate"] = stats["gps_found"] / stats["images_processed"]
            stats["location_match_rate"] = stats["locations_matched"] / stats["images_processed"]
            stats["error_rate"] = stats["errors"] / stats["images_processed"]
        
        return stats
    
    def get_coordinate_bounds(self, results: List[GPSResult]) -> Optional[Dict[str, float]]:
        """
        Get the bounding box of all GPS coordinates.
        
        Args:
            results: List of GPSResult objects
            
        Returns:
            Dictionary with min/max lat/lon or None if no coordinates found
        """
        valid_coords = [
            result.gps_coordinates 
            for result in results 
            if result.gps_coordinates is not None
        ]
        
        if not valid_coords:
            return None
        
        lats = [coord[0] for coord in valid_coords]
        lons = [coord[1] for coord in valid_coords]
        
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lon": min(lons),
            "max_lon": max(lons),
            "center_lat": sum(lats) / len(lats),
            "center_lon": sum(lons) / len(lons),
        }
    
    def cluster_by_location(
        self, 
        results: List[GPSResult],
        distance_threshold_km: float = 1.0
    ) -> Dict[str, List[GPSResult]]:
        """
        Cluster results by geographic proximity.
        
        Args:
            results: List of GPSResult objects
            distance_threshold_km: Maximum distance in km for clustering
            
        Returns:
            Dictionary mapping cluster names to lists of GPSResult objects
        """
        from sklearn.cluster import DBSCAN
        
        # Filter results with GPS coordinates
        valid_results = [
            result for result in results 
            if result.gps_coordinates is not None
        ]
        
        if not valid_results:
            return {}
        
        # Extract coordinates
        coordinates = np.array([result.gps_coordinates for result in valid_results])
        
        # Convert distance threshold to approximate degrees
        # (rough approximation: 1 degree ≈ 111 km)
        eps = distance_threshold_km / 111.0
        
        # Perform clustering
        clustering = DBSCAN(eps=eps, min_samples=1).fit(coordinates)
        
        # Group results by cluster
        clusters = {}
        for i, label in enumerate(clustering.labels_):
            cluster_name = f"cluster_{label}" if label != -1 else "outliers"
            if cluster_name not in clusters:
                clusters[cluster_name] = []
            clusters[cluster_name].append(valid_results[i])
        
        return clusters