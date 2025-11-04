"""
Utility functions for image processing and metadata extraction.
"""

from PIL import Image as PILImage
from PIL.ExifTags import TAGS
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
import os
import logging
from datetime import datetime
from .models import Image, ImageMetadata, GPSData
from .gps_service import gps_service

logger = logging.getLogger(__name__)


def extract_exif_data(image_path: str) -> dict:
    """
    Extract all EXIF data from an image.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary of EXIF data
    """
    try:
        img = PILImage.open(image_path)
        exif = img._getexif()

        if exif is None:
            return {}

        exif_data = {}
        for tag, value in exif.items():
            tag_name = TAGS.get(tag, tag)
            # Convert bytes to string for JSON serialization
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8')
                except:
                    value = str(value)
            exif_data[tag_name] = value

        return exif_data

    except Exception as e:
        logger.error(f"Error extracting EXIF from {image_path}: {e}")
        return {}


def extract_image_metadata(image_instance: Image):
    """
    Extract and save metadata for an Image instance.

    Args:
        image_instance: Image model instance
    """
    try:
        image_path = image_instance.file.path

        # Extract EXIF data
        exif_data = extract_exif_data(image_path)

        # Extract camera information
        camera_make = exif_data.get('Make', '')
        camera_model = exif_data.get('Model', '')

        # Extract date taken
        date_taken = None
        date_str = exif_data.get('DateTimeOriginal') or exif_data.get('DateTime')
        if date_str:
            try:
                date_taken = datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
            except:
                pass

        # Check for GPS data
        has_gps = 'GPSInfo' in exif_data

        # Create or update ImageMetadata
        metadata, created = ImageMetadata.objects.update_or_create(
            image=image_instance,
            defaults={
                'exif_data': exif_data,
                'has_gps': has_gps,
                'camera_make': camera_make,
                'camera_model': camera_model,
                'date_taken': date_taken,
            }
        )

        # Extract GPS data if available
        if has_gps:
            extract_gps_data(image_instance)

        logger.info(f"Extracted metadata for {image_instance.original_filename}")
        return metadata

    except Exception as e:
        logger.error(f"Error extracting metadata for {image_instance.original_filename}: {e}")
        return None


def extract_gps_data(image_instance: Image):
    """
    Extract and save GPS data for an Image instance.

    Args:
        image_instance: Image model instance
    """
    try:
        image_path = image_instance.file.path

        # Get GPS coordinates
        coords = gps_service.get_gps_coordinates(image_path)
        if coords is None:
            return None

        # Get altitude
        altitude = gps_service.get_altitude(image_path)

        # Create or update GPSData
        gps_data, created = GPSData.objects.update_or_create(
            image=image_instance,
            defaults={
                'latitude': coords[0],
                'longitude': coords[1],
                'altitude': altitude,
            }
        )

        logger.info(f"Extracted GPS data for {image_instance.original_filename}: {coords}")
        return gps_data

    except Exception as e:
        logger.error(f"Error extracting GPS for {image_instance.original_filename}: {e}")
        return None


def create_thumbnail(image_instance: Image, size=(300, 300)):
    """
    Create a thumbnail for an image.

    Args:
        image_instance: Image model instance
        size: Tuple of (width, height) for thumbnail

    Returns:
        Path to thumbnail file
    """
    try:
        from django.core.files.base import ContentFile
        from io import BytesIO

        # Open original image
        img = PILImage.open(image_instance.file.path)

        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Create thumbnail
        img.thumbnail(size, PILImage.Resampling.LANCZOS)

        # Save to BytesIO
        thumb_io = BytesIO()
        img.save(thumb_io, format='JPEG', quality=85)

        # Generate thumbnail filename
        base_name = os.path.splitext(image_instance.original_filename)[0]
        thumb_name = f"{base_name}_thumb.jpg"

        # Save to image instance
        image_instance.thumbnail.save(
            thumb_name,
            ContentFile(thumb_io.getvalue()),
            save=True
        )

        logger.info(f"Created thumbnail for {image_instance.original_filename}")
        return image_instance.thumbnail.path

    except Exception as e:
        logger.error(f"Error creating thumbnail for {image_instance.original_filename}: {e}")
        return None


def validate_image_upload(uploaded_file: UploadedFile) -> tuple:
    """
    Validate an uploaded image file.

    Args:
        uploaded_file: Django UploadedFile instance

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
        max_size_mb = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        return False, f"File too large. Maximum size is {max_size_mb}MB"

    # Check file extension
    ext = os.path.splitext(uploaded_file.name)[1].lower().replace('.', '')
    if ext.upper() not in settings.ALLOWED_IMAGE_FORMATS:
        return False, f"Invalid file format. Allowed formats: {', '.join(settings.ALLOWED_IMAGE_FORMATS)}"

    # Try to open with PIL to verify it's a valid image
    try:
        img = PILImage.open(uploaded_file)
        img.verify()
        uploaded_file.seek(0)  # Reset file pointer
    except Exception as e:
        return False, f"Invalid image file: {str(e)}"

    return True, ""


def get_image_dimensions(image_path: str) -> tuple:
    """
    Get dimensions of an image.

    Args:
        image_path: Path to image file

    Returns:
        Tuple of (width, height)
    """
    try:
        img = PILImage.open(image_path)
        return img.size
    except Exception as e:
        logger.error(f"Error getting dimensions for {image_path}: {e}")
        return (0, 0)
