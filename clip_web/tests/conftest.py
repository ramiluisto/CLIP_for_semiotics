"""
Pytest configuration and shared fixtures for CLIP for Humanists tests.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage
import io

from apps.projects.models import Project, ProjectMembership
from apps.images.models import ImageDataset, Image, ImageMetadata, GPSData
from apps.analysis.models import Analysis, TextPrompt, SimilarityResult

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def user2(db):
    """Create a second test user."""
    return User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123',
        first_name='Test2',
        last_name='User2'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def project(db, user):
    """Create a test project."""
    project = Project.objects.create(
        owner=user,
        name='Test Project',
        description='A test project for CLIP analysis',
        is_public=False,
        tags=['test', 'research']
    )
    # Create owner membership
    ProjectMembership.objects.create(
        project=project,
        user=user,
        role='owner'
    )
    return project


@pytest.fixture
def public_project(db, user):
    """Create a public test project."""
    project = Project.objects.create(
        owner=user,
        name='Public Test Project',
        description='A public test project',
        is_public=True
    )
    ProjectMembership.objects.create(
        project=project,
        user=user,
        role='owner'
    )
    return project


@pytest.fixture
def dataset(db, project):
    """Create a test image dataset."""
    return ImageDataset.objects.create(
        project=project,
        name='Test Dataset',
        description='A test dataset',
        created_by=project.owner
    )


@pytest.fixture
def create_test_image():
    """Factory fixture to create test images."""
    def _create_image(width=100, height=100, color='RGB'):
        """Create a simple test image."""
        image = PILImage.new(color, (width, height), color='blue')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return SimpleUploadedFile(
            name='test_image.png',
            content=buffer.read(),
            content_type='image/png'
        )
    return _create_image


@pytest.fixture
def image(db, dataset, create_test_image):
    """Create a test image in the dataset."""
    test_file = create_test_image()
    return Image.objects.create(
        dataset=dataset,
        file=test_file,
        original_filename='test_image.png',
        file_size=len(test_file),
        width=100,
        height=100,
        format='PNG',
        uploaded_by=dataset.created_by
    )


@pytest.fixture
def images(db, dataset, create_test_image):
    """Create multiple test images."""
    image_list = []
    for i in range(5):
        test_file = create_test_image()
        img = Image.objects.create(
            dataset=dataset,
            file=test_file,
            original_filename=f'test_image_{i}.png',
            file_size=len(test_file),
            width=100,
            height=100,
            format='PNG',
            uploaded_by=dataset.created_by
        )
        image_list.append(img)
    return image_list


@pytest.fixture
def image_with_gps(db, image):
    """Create an image with GPS data."""
    GPSData.objects.create(
        image=image,
        latitude=60.1699,
        longitude=24.9384,
        altitude=10.5,
        location_tag='Helsinki, Finland'
    )
    ImageMetadata.objects.create(
        image=image,
        has_gps=True,
        camera_make='Canon',
        camera_model='EOS 5D',
        exif_data={'Make': 'Canon', 'Model': 'EOS 5D'}
    )
    return image


@pytest.fixture
def analysis(db, project, dataset, user):
    """Create a test analysis."""
    analysis = Analysis.objects.create(
        project=project,
        dataset=dataset,
        name='Test Analysis',
        description='A test CLIP analysis',
        status='pending',
        created_by=user,
        model_name='openai/clip-vit-base-patch32',
        total_images=5
    )
    # Create text prompts
    prompts = ['architecture', 'nature', 'people']
    for idx, text in enumerate(prompts):
        TextPrompt.objects.create(
            analysis=analysis,
            text=text,
            order=idx
        )
    return analysis


@pytest.fixture
def completed_analysis(db, analysis, images):
    """Create a completed analysis with results."""
    analysis.status = 'completed'
    analysis.progress_percentage = 100
    analysis.images_processed = len(images)
    analysis.processing_time_seconds = 10.5
    analysis.save()

    # Create similarity results
    prompts = analysis.text_prompts.all()
    for image in images:
        for prompt in prompts:
            SimilarityResult.objects.create(
                analysis=analysis,
                image=image,
                text_prompt=prompt,
                similarity_score=0.75  # Mock score
            )
    return analysis


@pytest.fixture
def api_client():
    """Get DRF API test client."""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Get authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def mock_clip_service(mocker):
    """Mock the CLIP service for testing."""
    mock_service = mocker.patch('apps.analysis.clip_service.get_clip_service')
    mock_instance = mocker.Mock()
    mock_instance.compare_image_with_texts.return_value = {
        'architecture': 0.85,
        'nature': 0.65,
        'people': 0.45
    }
    mock_instance.get_model_name.return_value = 'openai/clip-vit-base-patch32'
    mock_instance.get_device.return_value = 'cpu'
    mock_service.return_value = mock_instance
    return mock_instance


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    """Use temporary media storage for tests."""
    settings.MEDIA_ROOT = tmpdir.strpath
