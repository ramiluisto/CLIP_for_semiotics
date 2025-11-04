"""
Image models for file management and metadata.
"""

from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from apps.projects.models import Project


class ImageDataset(models.Model):
    """
    Collection of images within a project.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='datasets'
    )
    name = models.CharField(
        max_length=255,
        help_text='Dataset name'
    )
    description = models.TextField(
        blank=True,
        help_text='Dataset description'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_datasets'
    )

    class Meta:
        verbose_name = 'Image Dataset'
        verbose_name_plural = 'Image Datasets'
        ordering = ['-created_at']
        unique_together = ('project', 'name')

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def get_image_count(self):
        """Get number of images in this dataset."""
        return self.images.count()

    def get_total_size(self):
        """Get total file size of all images in bytes."""
        total = self.images.aggregate(
            total=models.Sum('file_size')
        )['total']
        return total or 0


class Image(models.Model):
    """
    Individual image file with metadata.
    """
    dataset = models.ForeignKey(
        ImageDataset,
        on_delete=models.CASCADE,
        related_name='images'
    )
    file = models.ImageField(
        upload_to='uploads/%Y/%m/%d/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png']
            )
        ]
    )
    thumbnail = models.ImageField(
        upload_to='thumbnails/%Y/%m/%d/',
        blank=True,
        null=True
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.IntegerField(
        help_text='File size in bytes'
    )
    width = models.IntegerField()
    height = models.IntegerField()
    format = models.CharField(
        max_length=10,
        help_text='Image format (JPEG, PNG, etc.)'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_images'
    )

    class Meta:
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['dataset', '-uploaded_at']),
        ]

    def __str__(self):
        return self.original_filename

    def save(self, *args, **kwargs):
        """Extract image metadata before saving."""
        if self.file and not self.file_size:
            from PIL import Image as PILImage
            img = PILImage.open(self.file)
            self.width, self.height = img.size
            self.format = img.format
            self.file_size = self.file.size
        super().save(*args, **kwargs)


class ImageMetadata(models.Model):
    """
    EXIF and other metadata extracted from images.
    """
    image = models.OneToOneField(
        Image,
        on_delete=models.CASCADE,
        related_name='metadata'
    )
    exif_data = models.JSONField(
        default=dict,
        blank=True,
        help_text='Full EXIF data from image'
    )
    has_gps = models.BooleanField(
        default=False,
        help_text='Whether image contains GPS data'
    )
    camera_make = models.CharField(
        max_length=100,
        blank=True
    )
    camera_model = models.CharField(
        max_length=100,
        blank=True
    )
    date_taken = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Original date/time photo was taken'
    )
    extracted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Image Metadata'
        verbose_name_plural = 'Image Metadata'

    def __str__(self):
        return f"Metadata for {self.image.original_filename}"


class GPSData(models.Model):
    """
    GPS coordinates extracted from image EXIF data.
    """
    image = models.OneToOneField(
        Image,
        on_delete=models.CASCADE,
        related_name='gps_data'
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text='GPS latitude'
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text='GPS longitude'
    )
    altitude = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='GPS altitude in meters'
    )
    location_tag = models.CharField(
        max_length=255,
        blank=True,
        help_text='Named location or tag'
    )
    normalized_latitude = models.FloatField(
        null=True,
        blank=True,
        help_text='Normalized latitude (0-1 scale)'
    )
    normalized_longitude = models.FloatField(
        null=True,
        blank=True,
        help_text='Normalized longitude (0-1 scale)'
    )
    location_cluster = models.IntegerField(
        null=True,
        blank=True,
        help_text='Location cluster ID from KMeans'
    )
    extracted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'GPS Data'
        verbose_name_plural = 'GPS Data'
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"GPS for {self.image.original_filename}: ({self.latitude}, {self.longitude})"

    def get_coordinates_tuple(self):
        """Get coordinates as a tuple for calculations."""
        return (float(self.latitude), float(self.longitude))
