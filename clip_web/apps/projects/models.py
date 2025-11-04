"""
Project models for organizing analyses.
"""

from django.db import models
from django.conf import settings
from django.utils.text import slugify


class Project(models.Model):
    """
    Research project that contains multiple datasets and analyses.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects'
    )
    name = models.CharField(
        max_length=255,
        help_text='Project name'
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True
    )
    description = models.TextField(
        blank=True,
        help_text='Project description and goals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(
        default=False,
        help_text='Make project publicly viewable'
    )
    collaborators = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ProjectMembership',
        related_name='collaborated_projects',
        blank=True
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text='Project tags for organization'
    )

    class Meta:
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
            models.Index(fields=['owner', '-updated_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Project.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_analysis_count(self):
        """Get total number of analyses in this project."""
        return self.analyses.count()

    def get_image_count(self):
        """Get total number of images across all datasets."""
        from apps.images.models import Image
        return Image.objects.filter(
            dataset__project=self
        ).count()


class ProjectMembership(models.Model):
    """
    Through model for project collaborators with role-based access.
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('editor', 'Editor'),
        ('viewer', 'Viewer'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='project_memberships'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_invitations'
    )

    class Meta:
        verbose_name = 'Project Membership'
        verbose_name_plural = 'Project Memberships'
        unique_together = ('project', 'user')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} - {self.project.name} ({self.role})"

    def can_edit(self):
        """Check if user has edit permissions."""
        return self.role in ['owner', 'editor']

    def can_delete(self):
        """Check if user can delete project resources."""
        return self.role == 'owner'
