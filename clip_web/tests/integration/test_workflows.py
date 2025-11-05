"""
Integration tests for complete user workflows.
"""

import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.projects.models import Project, ProjectMembership
from apps.images.models import ImageDataset
from apps.analysis.models import Analysis

User = get_user_model()

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


class TestCompleteUserJourney:
    """Test complete user journey from registration to analysis."""

    def test_full_workflow(self, client, create_test_image):
        """Test complete workflow: register → create project → upload images → run analysis."""

        # Step 1: User registration
        register_url = reverse('accounts:register')
        register_data = {
            'username': 'researcher',
            'email': 'researcher@university.edu',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'institution': 'Test University',
            'research_area': 'Visual Semiotics'
        }
        response = client.post(register_url, register_data)
        assert response.status_code == 302
        user = User.objects.get(username='researcher')
        assert user is not None

        # Step 2: Login
        client.force_login(user)

        # Step 3: Create a project
        create_project_url = reverse('projects:create')
        project_data = {
            'name': 'Visual Culture Study',
            'description': 'Analyzing urban imagery',
            'is_public': False,
            'tags': '["urban", "architecture"]'
        }
        response = client.post(create_project_url, project_data)
        assert response.status_code == 302
        project = Project.objects.get(name='Visual Culture Study')
        assert project.owner == user

        # Step 4: Create a dataset
        create_dataset_url = reverse('images:dataset_create', kwargs={'project_slug': project.slug})
        dataset_data = {
            'name': 'Urban Photos',
            'description': 'Photos from city centers'
        }
        response = client.post(create_dataset_url, dataset_data)
        assert response.status_code == 302
        dataset = ImageDataset.objects.get(name='Urban Photos')

        # Step 5: Upload images (would be via AJAX in real usage)
        # Note: This is simplified - actual upload uses AJAX
        from apps.images.models import Image
        for i in range(3):
            test_file = create_test_image()
            Image.objects.create(
                dataset=dataset,
                file=test_file,
                original_filename=f'city_{i}.png',
                file_size=len(test_file),
                width=100,
                height=100,
                format='PNG',
                uploaded_by=user
            )
        assert dataset.images.count() == 3

        # Step 6: Create an analysis
        create_analysis_url = reverse('analysis:create', kwargs={'project_slug': project.slug})
        # This would normally be a POST, but we'll verify the page loads
        response = client.get(create_analysis_url)
        assert response.status_code == 200

        # Create analysis programmatically for testing
        analysis = Analysis.objects.create(
            project=project,
            dataset=dataset,
            name='Urban Analysis',
            description='Analyzing urban visual patterns',
            status='pending',
            created_by=user,
            model_name='openai/clip-vit-base-patch32',
            total_images=3
        )

        # Add text prompts
        from apps.analysis.models import TextPrompt
        prompts = ['architecture', 'people', 'vehicles']
        for idx, text in enumerate(prompts):
            TextPrompt.objects.create(
                analysis=analysis,
                text=text,
                order=idx
            )

        # Step 7: View analysis detail
        detail_url = reverse('analysis:detail', kwargs={
            'project_slug': project.slug,
            'analysis_id': analysis.id
        })
        response = client.get(detail_url)
        assert response.status_code == 200
        assert 'Urban Analysis' in response.content.decode()


class TestCollaborationWorkflow:
    """Test collaboration between multiple users."""

    def test_collaborative_project(self, client, user, user2, project):
        """Test adding collaborator and their access."""

        # Owner adds collaborator
        client.force_login(user)
        add_collab_url = reverse('projects:add_collaborator', kwargs={'slug': project.slug})
        data = {'email': user2.email, 'role': 'editor'}
        response = client.post(add_collab_url, data)
        assert response.status_code == 302

        # Verify membership created
        membership = ProjectMembership.objects.get(project=project, user=user2)
        assert membership.role == 'editor'

        # Collaborator can now access project
        client.force_login(user2)
        detail_url = reverse('projects:detail', kwargs={'slug': project.slug})
        response = client.get(detail_url)
        assert response.status_code == 200

        # Collaborator can create dataset
        dataset_url = reverse('images:dataset_create', kwargs={'project_slug': project.slug})
        dataset_data = {'name': 'Collab Dataset', 'description': 'Created by collaborator'}
        response = client.post(dataset_url, dataset_data)
        assert response.status_code == 302
        assert ImageDataset.objects.filter(name='Collab Dataset').exists()

        # But collaborator cannot delete project
        delete_url = reverse('projects:delete', kwargs={'slug': project.slug})
        response = client.get(delete_url)
        assert response.status_code == 403  # Forbidden


class TestDataManagementWorkflow:
    """Test data management operations."""

    def test_dataset_lifecycle(self, client, user, project, dataset, create_test_image):
        """Test complete dataset lifecycle."""
        client.force_login(user)

        # View dataset
        detail_url = reverse('images:dataset_detail', kwargs={
            'project_slug': project.slug,
            'dataset_id': dataset.id
        })
        response = client.get(detail_url)
        assert response.status_code == 200

        # Upload images
        from apps.images.models import Image
        for i in range(5):
            test_file = create_test_image()
            Image.objects.create(
                dataset=dataset,
                file=test_file,
                original_filename=f'test_{i}.png',
                file_size=len(test_file),
                width=100,
                height=100,
                format='PNG',
                uploaded_by=user
            )

        # Verify images in dataset
        response = client.get(detail_url)
        assert response.status_code == 200
        assert dataset.images.count() == 5

        # Update dataset
        update_url = reverse('images:dataset_update', kwargs={
            'project_slug': project.slug,
            'dataset_id': dataset.id
        })
        update_data = {'name': 'Updated Dataset Name', 'description': 'Updated description'}
        response = client.post(update_url, update_data)
        assert response.status_code == 302
        dataset.refresh_from_db()
        assert dataset.name == 'Updated Dataset Name'


class TestAnalysisWorkflow:
    """Test complete analysis workflow."""

    def test_analysis_lifecycle(self, client, user, project, dataset, images, mock_clip_service):
        """Test complete analysis lifecycle from creation to results."""
        client.force_login(user)

        # Create analysis
        analysis = Analysis.objects.create(
            project=project,
            dataset=dataset,
            name='Full Analysis Test',
            description='Testing complete workflow',
            status='pending',
            created_by=user,
            model_name='openai/clip-vit-base-patch32',
            total_images=len(images)
        )

        # Add prompts
        from apps.analysis.models import TextPrompt, SimilarityResult
        prompts_data = ['urban', 'nature', 'people']
        for idx, text in enumerate(prompts_data):
            TextPrompt.objects.create(
                analysis=analysis,
                text=text,
                order=idx
            )

        # Check analysis detail page
        detail_url = reverse('analysis:detail', kwargs={
            'project_slug': project.slug,
            'analysis_id': analysis.id
        })
        response = client.get(detail_url)
        assert response.status_code == 200
        assert 'pending' in response.content.decode().lower()

        # Simulate processing
        analysis.start_processing()
        analysis.progress_percentage = 50
        analysis.images_processed = 2
        analysis.save()

        # Check progress endpoint
        progress_url = reverse('analysis:progress', kwargs={
            'project_slug': project.slug,
            'analysis_id': analysis.id
        })
        response = client.get(progress_url)
        assert response.status_code == 200
        data = response.json()
        assert data['progress_percentage'] == 50

        # Complete analysis with results
        analysis.mark_completed()
        prompts = analysis.text_prompts.all()
        for image in images:
            for prompt in prompts:
                SimilarityResult.objects.create(
                    analysis=analysis,
                    image=image,
                    text_prompt=prompt,
                    similarity_score=0.85
                )

        # View results
        response = client.get(detail_url)
        assert response.status_code == 200
        assert 'completed' in response.content.decode().lower()


class TestErrorHandling:
    """Test error handling in workflows."""

    def test_invalid_project_access(self, client, user, user2):
        """Test accessing non-existent or forbidden project."""
        client.force_login(user2)

        # Try to access user's private project
        from apps.projects.models import Project
        private_project = Project.objects.create(
            owner=user,
            name='Private Project',
            is_public=False
        )
        ProjectMembership.objects.create(
            project=private_project,
            user=user,
            role='owner'
        )

        url = reverse('projects:detail', kwargs={'slug': private_project.slug})
        response = client.get(url)
        assert response.status_code == 403

        # Try to access non-existent project
        url = reverse('projects:detail', kwargs={'slug': 'nonexistent-slug'})
        response = client.get(url)
        assert response.status_code == 404

    def test_duplicate_dataset_name(self, client, user, project):
        """Test creating dataset with duplicate name."""
        client.force_login(user)

        # Create first dataset
        url = reverse('images:dataset_create', kwargs={'project_slug': project.slug})
        data = {'name': 'Unique Dataset', 'description': 'First'}
        response = client.post(url, data)
        assert response.status_code == 302

        # Try to create duplicate
        response = client.post(url, data)
        # Should show form with errors
        assert response.status_code == 200  # Form re-rendered with errors


class TestAPIWorkflow:
    """Test API-driven workflows."""

    def test_api_complete_workflow(self, authenticated_client, user, create_test_image):
        """Test creating project, dataset, and analysis via API."""

        # Create project
        url = reverse('api:project-list')
        project_data = {
            'name': 'API Test Project',
            'description': 'Created via API',
            'is_public': False,
            'tags': ['api', 'test']
        }
        response = authenticated_client.post(url, project_data, format='json')
        assert response.status_code == 201
        project_id = response.data['id']

        # Create dataset
        url = reverse('api:dataset-list')
        dataset_data = {
            'project': project_id,
            'name': 'API Dataset',
            'description': 'Test'
        }
        response = authenticated_client.post(url, dataset_data, format='json')
        assert response.status_code == 201
        dataset_id = response.data['id']

        # Create analysis
        url = reverse('api:analysis-list')
        analysis_data = {
            'project': project_id,
            'dataset': dataset_id,
            'name': 'API Analysis',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': ['test1', 'test2', 'test3']
        }
        response = authenticated_client.post(url, analysis_data, format='json')
        assert response.status_code == 201

        # Verify all created
        from apps.projects.models import Project
        from apps.images.models import ImageDataset
        from apps.analysis.models import Analysis
        assert Project.objects.filter(name='API Test Project').exists()
        assert ImageDataset.objects.filter(name='API Dataset').exists()
        assert Analysis.objects.filter(name='API Analysis').exists()
