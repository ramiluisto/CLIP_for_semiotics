"""
User models for CLIP for Humanists.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    """
    email = models.EmailField(
        unique=True,
        help_text='Email address for login and notifications'
    )
    institution = models.CharField(
        max_length=255,
        blank=True,
        help_text='Academic or research institution'
    )
    research_area = models.TextField(
        blank=True,
        help_text='Primary research area or field of study'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Override username requirement
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_storage_used(self):
        """Calculate total storage used by user's files."""
        from apps.images.models import Image
        total = Image.objects.filter(
            dataset__project__owner=self
        ).aggregate(
            total=models.Sum('file_size')
        )['total']
        return total or 0


class UserProfile(models.Model):
    """
    Extended user profile with additional settings and preferences.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='Profile picture'
    )
    bio = models.TextField(
        blank=True,
        help_text='Brief bio or research interests'
    )
    default_text_prompts = models.JSONField(
        default=list,
        blank=True,
        help_text='Default text prompts for new analyses'
    )
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text='User notification settings'
    )
    storage_quota_bytes = models.BigIntegerField(
        default=settings.DEFAULT_STORAGE_QUOTA,
        help_text='Storage quota in bytes'
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"Profile for {self.user.email}"

    def storage_usage_percentage(self):
        """Calculate percentage of storage quota used."""
        used = self.user.get_storage_used()
        if self.storage_quota_bytes == 0:
            return 100
        return (used / self.storage_quota_bytes) * 100

    def has_storage_available(self, required_bytes):
        """Check if user has enough storage for additional files."""
        used = self.user.get_storage_used()
        return (used + required_bytes) <= self.storage_quota_bytes
