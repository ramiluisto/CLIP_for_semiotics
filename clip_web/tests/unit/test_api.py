"""
Unit tests for REST API endpoints.
"""

import pytest
from django.urls import reverse
from rest_framework import status

pytestmark = [pytest.mark.api, pytest.mark.django_db]


class TestProjectAPI:
    """Tests for Project API endpoints."""

    def test_list_projects_unauthenticated(self, api_client):
        """Test listing projects without authentication."""
        url = reverse('api:project-list')
        response = api_client.get(url)
        # DRF returns 403 Forbidden instead of 401 Unauthorized for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_list_projects_authenticated(self, authenticated_client, project):
        """Test listing projects with authentication."""
        url = reverse('api:project-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Project'

    def test_create_project(self, authenticated_client):
        """Test creating a project via API."""
        url = reverse('api:project-list')
        data = {
            'name': 'API Test Project',
            'description': 'Created via API',
            'is_public': False,
            'tags': ['api', 'test']
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'API Test Project'

    def test_get_project_detail(self, authenticated_client, project):
        """Test retrieving project details."""
        url = reverse('api:project-detail', kwargs={'pk': project.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == project.name

    def test_update_project(self, authenticated_client, project):
        """Test updating a project."""
        url = reverse('api:project-detail', kwargs={'pk': project.id})
        data = {'name': 'Updated Name', 'description': 'Updated description'}
        response = authenticated_client.patch(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'

    def test_delete_project(self, authenticated_client, project):
        """Test deleting a project."""
        url = reverse('api:project-detail', kwargs={'pk': project.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_add_collaborator(self, authenticated_client, project, user2):
        """Test adding a collaborator to project."""
        url = reverse('api:project-add-collaborator', kwargs={'pk': project.id})
        data = {'user_id': user2.id, 'role': 'editor'}
        response = authenticated_client.post(url, data, format='json')
        # Returns 201 Created when creating new collaborator
        assert response.status_code == status.HTTP_201_CREATED


class TestImageDatasetAPI:
    """Tests for ImageDataset API endpoints."""

    def test_list_datasets(self, authenticated_client, dataset):
        """Test listing datasets."""
        url = reverse('api:dataset-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_create_dataset(self, authenticated_client, project):
        """Test creating a dataset."""
        url = reverse('api:dataset-list')
        data = {
            'project': project.id,
            'name': 'API Dataset',
            'description': 'Created via API'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'API Dataset'

    def test_get_dataset_detail(self, authenticated_client, dataset):
        """Test retrieving dataset details."""
        url = reverse('api:dataset-detail', kwargs={'pk': dataset.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == dataset.name


class TestImageAPI:
    """Tests for Image API endpoints."""

    def test_list_images(self, authenticated_client, images):
        """Test listing images."""
        url = reverse('api:image-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5

    def test_get_image_detail(self, authenticated_client, image):
        """Test retrieving image details."""
        url = reverse('api:image-detail', kwargs={'pk': image.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['original_filename'] == 'test_image.png'

    @pytest.mark.skip(reason="Requires CLIP model - integration test only")
    def test_semantic_search(self, authenticated_client, images, mock_clip_service):
        """Test semantic image search."""
        url = reverse('api:image-search')
        data = {'query': 'architecture', 'threshold': 0.5}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_200_OK
        # Mock service returns 0.85 for architecture
        assert len(response.data) > 0

    def test_filter_images_by_dataset(self, authenticated_client, images, dataset):
        """Test filtering images by dataset."""
        url = reverse('api:image-list')
        response = authenticated_client.get(url, {'dataset': dataset.id})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 5


class TestAnalysisAPI:
    """Tests for Analysis API endpoints."""

    def test_list_analyses(self, authenticated_client, analysis):
        """Test listing analyses."""
        url = reverse('api:analysis-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_create_analysis(self, authenticated_client, project, dataset):
        """Test creating an analysis."""
        url = reverse('api:analysis-list')
        data = {
            'project': project.id,
            'dataset': dataset.id,
            'name': 'API Analysis',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': ['test1', 'test2', 'test3']
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'API Analysis'

    def test_get_analysis_detail(self, authenticated_client, analysis):
        """Test retrieving analysis details."""
        url = reverse('api:analysis-detail', kwargs={'pk': analysis.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == analysis.name

    def test_get_analysis_progress(self, authenticated_client, analysis):
        """Test getting analysis progress."""
        url = reverse('api:analysis-progress', kwargs={'pk': analysis.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'progress_percentage' in response.data
        assert 'status' in response.data

    def test_get_analysis_results(self, authenticated_client, completed_analysis):
        """Test getting analysis results."""
        url = reverse('api:analysis-results', kwargs={'pk': completed_analysis.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) > 0

    def test_get_analysis_statistics(self, authenticated_client, completed_analysis):
        """Test getting analysis statistics."""
        url = reverse('api:analysis-statistics', kwargs={'pk': completed_analysis.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'total_results' in response.data
        assert 'average_similarity' in response.data

    def test_filter_analyses_by_status(self, authenticated_client, analysis, completed_analysis):
        """Test filtering analyses by status."""
        url = reverse('api:analysis-list')
        response = authenticated_client.get(url, {'status': 'completed'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1


class TestPermissions:
    """Tests for API permissions."""

    def test_cannot_access_others_project(self, authenticated_client, user2):
        """Test that users cannot access other users' private projects."""
        from apps.projects.models import Project
        other_project = Project.objects.create(
            owner=user2,
            name='Other Project',
            is_public=False
        )
        url = reverse('api:project-detail', kwargs={'pk': other_project.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_can_access_public_project(self, authenticated_client, public_project):
        """Test that users can access public projects."""
        url = reverse('api:project-detail', kwargs={'pk': public_project.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_cannot_delete_others_project(self, authenticated_client, user2):
        """Test that users cannot delete other users' projects."""
        from apps.projects.models import Project
        other_project = Project.objects.create(
            owner=user2,
            name='Other Project'
        )
        url = reverse('api:project-detail', kwargs={'pk': other_project.id})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_collaborator_can_view_project(self, api_client, project, user2):
        """Test that collaborators can view projects."""
        # Add user2 as collaborator
        from apps.projects.models import ProjectMembership
        ProjectMembership.objects.create(
            project=project,
            user=user2,
            role='viewer'
        )
        # Authenticate as user2
        api_client.force_authenticate(user=user2)
        url = reverse('api:project-detail', kwargs={'pk': project.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_viewer_cannot_delete_project(self, api_client, project, user2):
        """Test that viewers cannot delete projects."""
        from apps.projects.models import ProjectMembership
        ProjectMembership.objects.create(
            project=project,
            user=user2,
            role='viewer'
        )
        api_client.force_authenticate(user=user2)
        url = reverse('api:project-detail', kwargs={'pk': project.id})
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPagination:
    """Tests for API pagination."""

    def test_pagination_works(self, authenticated_client, project, user):
        """Test that pagination works correctly."""
        from apps.images.models import ImageDataset
        # Create more datasets than page size
        for i in range(15):
            ImageDataset.objects.create(
                project=project,
                name=f'Dataset {i}',
                created_by=user
            )
        url = reverse('api:dataset-list')
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert 'count' in response.data
        assert 'next' in response.data
        assert response.data['count'] == 16  # 15 + 1 from fixture


class TestSearchAndFiltering:
    """Tests for search and filtering."""

    def test_search_projects_by_name(self, authenticated_client, project):
        """Test searching projects by name."""
        url = reverse('api:project-list')
        response = authenticated_client.get(url, {'search': 'Test'})
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1

    def test_filter_by_tags(self, authenticated_client, project):
        """Test filtering projects by tags."""
        url = reverse('api:project-list')
        response = authenticated_client.get(url, {'tags': 'test'})
        assert response.status_code == status.HTTP_200_OK
        # Should find the project with 'test' tag
        assert len(response.data['results']) >= 1
