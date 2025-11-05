"""
Unit tests for Django models.
"""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.projects.models import Project, ProjectMembership
from apps.images.models import ImageDataset, Image, GPSData, ImageMetadata
from apps.analysis.models import Analysis, TextPrompt, SimilarityResult

User = get_user_model()

pytestmark = pytest.mark.unit


class TestUserModel:
    """Tests for User model."""

    @pytest.mark.django_db
    def test_user_creation(self):
        """Test creating a user."""
        user = User.objects.create_user(
            username='newuser',
            email='newuser@example.com',
            password='password123'
        )
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'
        assert user.check_password('password123')

    @pytest.mark.django_db
    def test_user_profile_created(self, user):
        """Test that UserProfile is automatically created."""
        assert hasattr(user, 'profile')
        assert user.profile is not None

    @pytest.mark.django_db
    def test_superuser_creation(self):
        """Test creating a superuser."""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        assert admin.is_superuser
        assert admin.is_staff


class TestProjectModel:
    """Tests for Project model."""

    @pytest.mark.django_db
    def test_project_creation(self, user):
        """Test creating a project."""
        project = Project.objects.create(
            owner=user,
            name='My Project',
            description='Test description',
            is_public=False
        )
        assert project.name == 'My Project'
        assert project.owner == user
        assert project.slug is not None

    @pytest.mark.django_db
    def test_project_slug_generation(self, user):
        """Test automatic slug generation."""
        project = Project.objects.create(
            owner=user,
            name='Test Project Name'
        )
        assert project.slug == 'test-project-name'

    @pytest.mark.django_db
    def test_project_slug_uniqueness(self, user):
        """Test slug uniqueness with counter."""
        project1 = Project.objects.create(owner=user, name='Same Name')
        project2 = Project.objects.create(owner=user, name='Same Name')
        assert project1.slug == 'same-name'
        assert project2.slug == 'same-name-1'

    @pytest.mark.django_db
    def test_project_get_analysis_count(self, project, analysis):
        """Test getting analysis count."""
        assert project.get_analysis_count() == 1

    @pytest.mark.django_db
    def test_project_get_image_count(self, project, images):
        """Test getting total image count."""
        assert project.get_image_count() == 5


class TestProjectMembershipModel:
    """Tests for ProjectMembership model."""

    @pytest.mark.django_db
    def test_membership_creation(self, project, user2):
        """Test creating a project membership."""
        membership = ProjectMembership.objects.create(
            project=project,
            user=user2,
            role='editor',
            invited_by=project.owner
        )
        assert membership.role == 'editor'
        assert membership.user == user2

    @pytest.mark.django_db
    def test_membership_unique_together(self, project, user):
        """Test unique_together constraint."""
        # First membership already exists from project fixture
        with pytest.raises(IntegrityError):
            ProjectMembership.objects.create(
                project=project,
                user=user,
                role='editor'
            )

    @pytest.mark.django_db
    def test_can_edit_permission(self, project, user2):
        """Test can_edit permission method."""
        editor = ProjectMembership.objects.create(
            project=project,
            user=user2,
            role='editor'
        )
        assert editor.can_edit()

        viewer = ProjectMembership.objects.create(
            project=project,
            user=User.objects.create_user('viewer', 'v@test.com', 'pass'),
            role='viewer'
        )
        assert not viewer.can_edit()

    @pytest.mark.django_db
    def test_can_delete_permission(self, project, user2):
        """Test can_delete permission method."""
        owner_membership = project.memberships.get(user=project.owner)
        assert owner_membership.can_delete()

        editor = ProjectMembership.objects.create(
            project=project,
            user=user2,
            role='editor'
        )
        assert not editor.can_delete()


class TestImageDatasetModel:
    """Tests for ImageDataset model."""

    @pytest.mark.django_db
    def test_dataset_creation(self, project, user):
        """Test creating an image dataset."""
        dataset = ImageDataset.objects.create(
            project=project,
            name='My Dataset',
            description='Test dataset',
            created_by=user
        )
        assert dataset.name == 'My Dataset'
        assert dataset.project == project

    @pytest.mark.django_db
    def test_dataset_unique_name_per_project(self, project):
        """Test unique name constraint per project."""
        ImageDataset.objects.create(
            project=project,
            name='Dataset 1',
            created_by=project.owner
        )
        with pytest.raises(IntegrityError):
            ImageDataset.objects.create(
                project=project,
                name='Dataset 1',
                created_by=project.owner
            )

    @pytest.mark.django_db
    def test_dataset_get_image_count(self, dataset, images):
        """Test getting image count."""
        assert dataset.get_image_count() == 5

    @pytest.mark.django_db
    def test_dataset_get_total_size(self, dataset, images):
        """Test getting total file size."""
        total_size = dataset.get_total_size()
        assert total_size > 0


class TestImageModel:
    """Tests for Image model."""

    @pytest.mark.django_db
    def test_image_creation(self, image):
        """Test creating an image."""
        assert image.original_filename == 'test_image.png'
        assert image.width == 100
        assert image.height == 100
        assert image.format == 'PNG'

    @pytest.mark.django_db
    def test_image_with_gps_data(self, image_with_gps):
        """Test image with GPS data."""
        assert hasattr(image_with_gps, 'gps_data')
        assert image_with_gps.gps_data.latitude == 60.1699
        assert image_with_gps.gps_data.longitude == 24.9384

    @pytest.mark.django_db
    def test_image_with_metadata(self, image_with_gps):
        """Test image with metadata."""
        assert hasattr(image_with_gps, 'metadata')
        assert image_with_gps.metadata.has_gps
        assert image_with_gps.metadata.camera_make == 'Canon'


class TestGPSDataModel:
    """Tests for GPSData model."""

    @pytest.mark.django_db
    def test_gps_data_creation(self, image):
        """Test creating GPS data."""
        gps = GPSData.objects.create(
            image=image,
            latitude=51.5074,
            longitude=-0.1278,
            altitude=11.0,
            location_tag='London, UK'
        )
        assert gps.latitude == 51.5074
        assert gps.longitude == -0.1278

    @pytest.mark.django_db
    def test_get_coordinates_tuple(self, image_with_gps):
        """Test getting coordinates as tuple."""
        coords = image_with_gps.gps_data.get_coordinates_tuple()
        assert coords == (60.1699, 24.9384)


class TestAnalysisModel:
    """Tests for Analysis model."""

    @pytest.mark.django_db
    def test_analysis_creation(self, analysis):
        """Test creating an analysis."""
        assert analysis.name == 'Test Analysis'
        assert analysis.status == 'pending'
        assert analysis.model_name == 'openai/clip-vit-base-patch32'

    @pytest.mark.django_db
    def test_analysis_text_prompts(self, analysis):
        """Test analysis text prompts."""
        prompts = list(analysis.text_prompts.values_list('text', flat=True))
        assert 'architecture' in prompts
        assert 'nature' in prompts
        assert 'people' in prompts

    @pytest.mark.django_db
    def test_analysis_start_processing(self, analysis):
        """Test starting analysis processing."""
        analysis.start_processing()
        assert analysis.status == 'processing'
        assert analysis.started_at is not None

    @pytest.mark.django_db
    def test_analysis_mark_completed(self, analysis):
        """Test marking analysis as completed."""
        analysis.start_processing()
        analysis.mark_completed()
        assert analysis.status == 'completed'
        assert analysis.progress_percentage == 100
        assert analysis.completed_at is not None
        assert analysis.processing_time_seconds is not None

    @pytest.mark.django_db
    def test_analysis_mark_failed(self, analysis):
        """Test marking analysis as failed."""
        error_msg = 'Test error'
        analysis.mark_failed(error_msg)
        assert analysis.status == 'failed'
        assert analysis.error_message == error_msg

    @pytest.mark.django_db
    def test_analysis_get_progress_display(self, analysis):
        """Test getting progress display."""
        analysis.total_images = 10
        analysis.images_processed = 5
        analysis.progress_percentage = 50
        display = analysis.get_progress_display()
        assert '5/10' in display
        assert '50%' in display


class TestTextPromptModel:
    """Tests for TextPrompt model."""

    @pytest.mark.django_db
    def test_text_prompt_creation(self, analysis):
        """Test creating a text prompt."""
        prompt = TextPrompt.objects.create(
            analysis=analysis,
            text='test prompt',
            order=10
        )
        assert prompt.text == 'test prompt'
        assert prompt.order == 10

    @pytest.mark.django_db
    def test_text_prompt_unique_per_analysis(self, analysis):
        """Test unique constraint for prompts in analysis."""
        # One 'architecture' prompt already exists from fixture
        with pytest.raises(IntegrityError):
            TextPrompt.objects.create(
                analysis=analysis,
                text='architecture',
                order=5
            )


class TestSimilarityResultModel:
    """Tests for SimilarityResult model."""

    @pytest.mark.django_db
    def test_similarity_result_creation(self, analysis, image):
        """Test creating a similarity result."""
        prompt = analysis.text_prompts.first()
        result = SimilarityResult.objects.create(
            analysis=analysis,
            image=image,
            text_prompt=prompt,
            similarity_score=0.85
        )
        assert result.similarity_score == 0.85

    @pytest.mark.django_db
    def test_similarity_result_get_score_percentage(self, completed_analysis):
        """Test converting score to percentage."""
        result = completed_analysis.results.first()
        percentage = result.get_score_percentage()
        # Score 0.75 -> (0.75 + 1) / 2 * 100 = 87.5
        assert percentage == 87.5

    @pytest.mark.django_db
    def test_similarity_result_unique_together(self, analysis, image):
        """Test unique_together constraint."""
        prompt = analysis.text_prompts.first()
        SimilarityResult.objects.create(
            analysis=analysis,
            image=image,
            text_prompt=prompt,
            similarity_score=0.7
        )
        with pytest.raises(IntegrityError):
            SimilarityResult.objects.create(
                analysis=analysis,
                image=image,
                text_prompt=prompt,
                similarity_score=0.8
            )
