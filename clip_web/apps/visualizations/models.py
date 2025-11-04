"""
Visualization models for charts, maps, and exports.
"""

from django.db import models
from django.conf import settings
from apps.analysis.models import Analysis
import os


class Visualization(models.Model):
    """
    Generated visualization (chart, map, etc.) for an analysis.
    """
    VIZ_TYPES = [
        ('heatmap', 'Similarity Heatmap'),
        ('map', 'GPS Map'),
        ('correlation', 'Correlation Matrix'),
        ('violin', 'Violin Plot'),
        ('location_corr', 'Location Correlation'),
        ('image_grid', 'Image Grid'),
        ('bar_chart', 'Bar Chart'),
        ('scatter', 'Scatter Plot'),
    ]

    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='visualizations'
    )
    viz_type = models.CharField(
        max_length=50,
        choices=VIZ_TYPES,
        help_text='Type of visualization'
    )
    title = models.CharField(
        max_length=255,
        help_text='Visualization title'
    )
    file_path = models.CharField(
        max_length=500,
        help_text='Path to generated file'
    )
    file_format = models.CharField(
        max_length=10,
        default='png',
        help_text='File format (png, html, svg, etc.)'
    )
    config = models.JSONField(
        default=dict,
        blank=True,
        help_text='Visualization-specific parameters'
    )
    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text='File size in bytes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_visualizations'
    )

    class Meta:
        verbose_name = 'Visualization'
        verbose_name_plural = 'Visualizations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['analysis', '-created_at']),
            models.Index(fields=['viz_type']),
        ]

    def __str__(self):
        return f"{self.get_viz_type_display()}: {self.title}"

    def get_file_url(self):
        """Get URL for accessing the visualization file."""
        from django.conf import settings
        if self.file_path.startswith(settings.MEDIA_URL):
            return self.file_path
        return os.path.join(settings.MEDIA_URL, self.file_path)

    def delete(self, *args, **kwargs):
        """Delete the file when model instance is deleted."""
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError:
                pass
        super().delete(*args, **kwargs)


class ExportJob(models.Model):
    """
    Export job for packaging analysis results.
    """
    EXPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('zip', 'ZIP Archive'),
        ('pdf', 'PDF Report'),
        ('excel', 'Excel Spreadsheet'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='exports'
    )
    format = models.CharField(
        max_length=20,
        choices=EXPORT_FORMATS,
        help_text='Export format'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Path to generated export file'
    )
    file_size = models.IntegerField(
        null=True,
        blank=True,
        help_text='File size in bytes'
    )
    include_images = models.BooleanField(
        default=False,
        help_text='Include original images in export'
    )
    include_visualizations = models.BooleanField(
        default=True,
        help_text='Include visualizations in export'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_exports'
    )
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Celery task ID for tracking'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if export failed'
    )

    class Meta:
        verbose_name = 'Export Job'
        verbose_name_plural = 'Export Jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.analysis.name} - {self.get_format_display()} ({self.status})"

    def get_file_url(self):
        """Get URL for downloading the export file."""
        from django.conf import settings
        if self.file_path:
            return os.path.join(settings.MEDIA_URL, self.file_path)
        return None

    def delete(self, *args, **kwargs):
        """Delete the file when model instance is deleted."""
        if self.file_path and os.path.exists(self.file_path):
            try:
                os.remove(self.file_path)
            except OSError:
                pass
        super().delete(*args, **kwargs)
