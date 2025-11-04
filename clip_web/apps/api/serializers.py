"""
API Serializers for CLIP for Humanists.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
from apps.projects.models import Project, ProjectMembership
from apps.images.models import ImageDataset, Image, ImageMetadata, GPSData
from apps.analysis.models import Analysis, TextPrompt, SimilarityResult
from apps.visualizations.models import Visualization, ExportJob

User = get_user_model()


# User Serializers
class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'institution', 'research_area', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile model."""
    user = UserSerializer(read_only=True)
    storage_used = serializers.SerializerMethodField()
    storage_percentage = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = ['user', 'avatar', 'bio', 'default_text_prompts',
                  'storage_quota_bytes', 'storage_used', 'storage_percentage']

    def get_storage_used(self, obj):
        """Get storage used in bytes."""
        return obj.user.get_storage_used()

    def get_storage_percentage(self, obj):
        """Get storage usage percentage."""
        return obj.storage_usage_percentage()


# Project Serializers
class ProjectMembershipSerializer(serializers.ModelSerializer):
    """Serializer for ProjectMembership."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = ProjectMembership
        fields = ['id', 'user', 'role', 'joined_at']


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project lists."""
    owner = UserSerializer(read_only=True)
    analysis_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'slug', 'description', 'owner',
                  'created_at', 'updated_at', 'is_public', 'tags',
                  'analysis_count', 'image_count']

    def get_analysis_count(self, obj):
        return obj.get_analysis_count()

    def get_image_count(self, obj):
        return obj.get_image_count()


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for project detail view."""
    owner = UserSerializer(read_only=True)
    memberships = ProjectMembershipSerializer(many=True, read_only=True)
    analysis_count = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'slug', 'description', 'owner',
                  'created_at', 'updated_at', 'is_public', 'tags',
                  'memberships', 'analysis_count', 'image_count']

    def get_analysis_count(self, obj):
        return obj.get_analysis_count()

    def get_image_count(self, obj):
        return obj.get_image_count()


# Image Serializers
class GPSDataSerializer(serializers.ModelSerializer):
    """Serializer for GPSData."""

    class Meta:
        model = GPSData
        fields = ['latitude', 'longitude', 'altitude', 'location_tag',
                  'normalized_latitude', 'normalized_longitude', 'location_cluster']


class ImageMetadataSerializer(serializers.ModelSerializer):
    """Serializer for ImageMetadata."""

    class Meta:
        model = ImageMetadata
        fields = ['exif_data', 'has_gps', 'camera_make', 'camera_model', 'date_taken']


class ImageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for image lists."""
    has_gps = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['id', 'file', 'thumbnail', 'original_filename',
                  'file_size', 'width', 'height', 'format',
                  'uploaded_at', 'has_gps']

    def get_has_gps(self, obj):
        return hasattr(obj, 'metadata') and obj.metadata.has_gps


class ImageDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for image detail view."""
    metadata = ImageMetadataSerializer(read_only=True)
    gps_data = GPSDataSerializer(read_only=True)

    class Meta:
        model = Image
        fields = ['id', 'file', 'thumbnail', 'original_filename',
                  'file_size', 'width', 'height', 'format',
                  'uploaded_at', 'metadata', 'gps_data']


class ImageDatasetListSerializer(serializers.ModelSerializer):
    """Serializer for dataset lists."""
    image_count = serializers.SerializerMethodField()
    total_size = serializers.SerializerMethodField()

    class Meta:
        model = ImageDataset
        fields = ['id', 'name', 'description', 'created_at',
                  'image_count', 'total_size']

    def get_image_count(self, obj):
        return obj.get_image_count()

    def get_total_size(self, obj):
        return obj.get_total_size()


class ImageDatasetDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for dataset detail view."""
    images = ImageListSerializer(many=True, read_only=True)
    image_count = serializers.SerializerMethodField()
    total_size = serializers.SerializerMethodField()

    class Meta:
        model = ImageDataset
        fields = ['id', 'name', 'description', 'created_at',
                  'images', 'image_count', 'total_size']

    def get_image_count(self, obj):
        return obj.get_image_count()

    def get_total_size(self, obj):
        return obj.get_total_size()


# Analysis Serializers
class TextPromptSerializer(serializers.ModelSerializer):
    """Serializer for TextPrompt."""

    class Meta:
        model = TextPrompt
        fields = ['id', 'text', 'order', 'created_at']


class SimilarityResultSerializer(serializers.ModelSerializer):
    """Serializer for SimilarityResult."""
    image = ImageListSerializer(read_only=True)
    text_prompt = TextPromptSerializer(read_only=True)

    class Meta:
        model = SimilarityResult
        fields = ['id', 'image', 'text_prompt', 'similarity_score', 'created_at']


class AnalysisListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for analysis lists."""
    project_name = serializers.CharField(source='project.name', read_only=True)
    dataset_name = serializers.CharField(source='dataset.name', read_only=True)
    prompt_count = serializers.SerializerMethodField()

    class Meta:
        model = Analysis
        fields = ['id', 'name', 'description', 'status', 'project_name',
                  'dataset_name', 'created_at', 'started_at', 'completed_at',
                  'progress_percentage', 'images_processed', 'total_images',
                  'prompt_count']

    def get_prompt_count(self, obj):
        return obj.text_prompts.count()


class AnalysisDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for analysis detail view."""
    project = ProjectListSerializer(read_only=True)
    dataset = ImageDatasetListSerializer(read_only=True)
    text_prompts = TextPromptSerializer(many=True, read_only=True)
    created_by = UserSerializer(read_only=True)
    progress_display = serializers.SerializerMethodField()

    class Meta:
        model = Analysis
        fields = ['id', 'project', 'dataset', 'name', 'description',
                  'status', 'created_at', 'started_at', 'completed_at',
                  'created_by', 'model_name', 'progress_percentage',
                  'images_processed', 'total_images', 'processing_time_seconds',
                  'text_prompts', 'error_message', 'progress_display']

    def get_progress_display(self, obj):
        return obj.get_progress_display()


class AnalysisCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new analysis."""
    text_prompts = serializers.ListField(
        child=serializers.CharField(max_length=500),
        write_only=True
    )

    class Meta:
        model = Analysis
        fields = ['project', 'dataset', 'name', 'description', 'text_prompts']

    def create(self, validated_data):
        text_prompts_data = validated_data.pop('text_prompts')
        user = self.context['request'].user

        # Create analysis
        analysis = Analysis.objects.create(
            created_by=user,
            **validated_data
        )

        # Create text prompts
        for idx, prompt_text in enumerate(text_prompts_data):
            TextPrompt.objects.create(
                analysis=analysis,
                text=prompt_text,
                order=idx
            )

        return analysis


# Visualization Serializers
class VisualizationSerializer(serializers.ModelSerializer):
    """Serializer for Visualization."""
    file_url = serializers.SerializerMethodField()
    viz_type_display = serializers.CharField(source='get_viz_type_display', read_only=True)

    class Meta:
        model = Visualization
        fields = ['id', 'viz_type', 'viz_type_display', 'title',
                  'file_path', 'file_url', 'file_format', 'file_size',
                  'config', 'created_at']

    def get_file_url(self, obj):
        return obj.get_file_url()


class ExportJobSerializer(serializers.ModelSerializer):
    """Serializer for ExportJob."""
    file_url = serializers.SerializerMethodField()
    format_display = serializers.CharField(source='get_format_display', read_only=True)

    class Meta:
        model = ExportJob
        fields = ['id', 'format', 'format_display', 'status',
                  'file_path', 'file_url', 'file_size',
                  'include_images', 'include_visualizations',
                  'created_at', 'completed_at', 'error_message']

    def get_file_url(self, obj):
        return obj.get_file_url()


# Search and Filter Serializers
class ImageSearchResultSerializer(serializers.Serializer):
    """Serializer for image search results."""
    image = ImageDetailSerializer()
    similarity_score = serializers.FloatField()
    matched_concepts = serializers.ListField(child=serializers.CharField())


class AnalysisStatisticsSerializer(serializers.Serializer):
    """Serializer for analysis statistics."""
    concept = serializers.CharField()
    mean_score = serializers.FloatField()
    median_score = serializers.FloatField()
    std_dev = serializers.FloatField()
    min_score = serializers.FloatField()
    max_score = serializers.FloatField()
    count = serializers.IntegerField()
