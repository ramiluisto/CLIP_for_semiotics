"""
Analysis models for CLIP processing.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.projects.models import Project
from apps.images.models import ImageDataset, Image


class Analysis(models.Model):
    """
    CLIP analysis job that compares images with text prompts.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='analyses'
    )
    dataset = models.ForeignKey(
        ImageDataset,
        on_delete=models.CASCADE,
        related_name='analyses'
    )
    name = models.CharField(
        max_length=255,
        help_text='Analysis name'
    )
    description = models.TextField(
        blank=True,
        help_text='Analysis description and goals'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_analyses'
    )

    # Processing details
    model_name = models.CharField(
        max_length=100,
        default='openai/clip-vit-base-patch32',
        help_text='CLIP model used for analysis'
    )
    celery_task_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='Celery task ID for tracking'
    )
    progress_percentage = models.IntegerField(
        default=0,
        help_text='Processing progress (0-100)'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if analysis failed'
    )

    # Results summary
    images_processed = models.IntegerField(
        default=0,
        help_text='Number of images successfully processed'
    )
    total_images = models.IntegerField(
        default=0,
        help_text='Total number of images to process'
    )
    processing_time_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text='Total processing time in seconds'
    )

    class Meta:
        verbose_name = 'Analysis'
        verbose_name_plural = 'Analyses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    def start_processing(self):
        """Mark analysis as started."""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save()

    def mark_completed(self):
        """Mark analysis as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        if self.started_at:
            self.processing_time_seconds = (
                self.completed_at - self.started_at
            ).total_seconds()
        self.save()

    def mark_failed(self, error_message):
        """Mark analysis as failed with error message."""
        self.status = 'failed'
        self.error_message = error_message
        self.save()

    def get_progress_display(self):
        """Get human-readable progress display."""
        if self.total_images == 0:
            return "Initializing..."
        return f"{self.images_processed}/{self.total_images} images ({self.progress_percentage}%)"


class TextPrompt(models.Model):
    """
    Text prompt/keyword used for comparing with images.
    """
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='text_prompts'
    )
    text = models.CharField(
        max_length=500,
        help_text='Text prompt or keyword'
    )
    order = models.IntegerField(
        default=0,
        help_text='Display order'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Text Prompt'
        verbose_name_plural = 'Text Prompts'
        ordering = ['analysis', 'order', 'id']
        unique_together = ('analysis', 'text')

    def __str__(self):
        return f"{self.analysis.name}: {self.text}"


class SimilarityResult(models.Model):
    """
    Result of comparing an image with a text prompt using CLIP.
    """
    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name='results'
    )
    image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name='similarity_results'
    )
    text_prompt = models.ForeignKey(
        TextPrompt,
        on_delete=models.CASCADE,
        related_name='results'
    )
    similarity_score = models.FloatField(
        help_text='CLIP similarity score (-1 to 1)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Similarity Result'
        verbose_name_plural = 'Similarity Results'
        unique_together = ('analysis', 'image', 'text_prompt')
        indexes = [
            models.Index(fields=['analysis', 'similarity_score']),
            models.Index(fields=['text_prompt', 'similarity_score']),
            models.Index(fields=['image', 'analysis']),
        ]

    def __str__(self):
        return f"{self.image.original_filename} - {self.text_prompt.text}: {self.similarity_score:.3f}"

    def get_score_percentage(self):
        """Convert similarity score to percentage (0-100)."""
        # Convert from -1 to 1 range to 0 to 100 range
        return ((self.similarity_score + 1) / 2) * 100
