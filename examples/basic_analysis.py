"""
Basic example of using CLIP for Humanists Django Application.

This example demonstrates how to programmatically:
1. Create a project and dataset
2. Upload images
3. Run a CLIP analysis
4. Generate visualizations

Note: This requires Django to be running and properly configured.
For API usage, see examples/api_usage.py
"""

import os
import sys
import django

# Add the Django project to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'clip_web'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.projects.models import Project
from apps.images.models import ImageDataset, Image
from apps.analysis.models import Analysis, TextPrompt
from apps.visualizations.generators import (
    HeatmapGenerator,
    CorrelationMatrixGenerator,
    ImageGridGenerator
)

User = get_user_model()

def main():
    """Run a basic CLIP analysis workflow."""

    print("=" * 60)
    print("CLIP for Humanists - Basic Analysis Example")
    print("=" * 60)

    # Check if database is migrated
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM accounts_user LIMIT 1")
    except Exception:
        print("\n❌ Database not migrated!")
        print("\nPlease run migrations first:")
        print("  cd clip_web")
        print("  python manage.py migrate")
        print("  python manage.py createsuperuser")
        print("\nThen run this script again.")
        return

    # 1. Get or create a user
    print("\n1. Setting up user...")
    user, created = User.objects.get_or_create(
        username='example_user',
        defaults={
            'email': 'example@example.com',
            'first_name': 'Example',
            'last_name': 'User'
        }
    )
    if created:
        user.set_password('example_password')
        user.save()
        print(f"   Created user: {user.username}")
    else:
        print(f"   Using existing user: {user.username}")

    # 2. Create a project
    print("\n2. Creating project...")
    project, created = Project.objects.get_or_create(
        owner=user,
        name='Example Analysis Project',
        defaults={
            'description': 'An example project demonstrating CLIP analysis',
            'is_public': False
        }
    )
    if created:
        print(f"   Created project: {project.name}")
    else:
        print(f"   Using existing project: {project.name}")

    # 3. Create a dataset
    print("\n3. Creating dataset...")
    dataset, created = ImageDataset.objects.get_or_create(
        project=project,
        name='Example Dataset',
        defaults={
            'description': 'Example images for CLIP analysis',
            'created_by': user
        }
    )
    if created:
        print(f"   Created dataset: {dataset.name}")
    else:
        print(f"   Using existing dataset: {dataset.name}")

    # 4. Check for images
    print("\n4. Checking for images...")
    image_count = dataset.images.count()
    print(f"   Dataset has {image_count} images")

    if image_count == 0:
        print("\n   ⚠️  No images found in dataset!")
        print("   Please upload images through:")
        print("   - Web UI: http://localhost:8000/projects/")
        print("   - API: POST /api/v1/datasets/{id}/upload/")
        print("   - Django admin: http://localhost:8000/admin/")
        return

    # 5. Create an analysis
    print("\n5. Creating analysis...")
    analysis, created = Analysis.objects.get_or_create(
        project=project,
        dataset=dataset,
        name='Example CLIP Analysis',
        defaults={
            'description': 'Analyzing images with CLIP',
            'created_by': user,
            'model_name': 'openai/clip-vit-base-patch32',
            'total_images': image_count,
            'status': 'pending'
        }
    )
    if created:
        print(f"   Created analysis: {analysis.name}")

        # Add text prompts
        prompts = ['scary', 'friendly', 'warning', 'information', 'official']
        print(f"\n6. Adding {len(prompts)} text prompts...")
        for idx, text in enumerate(prompts):
            TextPrompt.objects.get_or_create(
                analysis=analysis,
                text=text,
                defaults={'order': idx}
            )
        print(f"   Prompts: {', '.join(prompts)}")
    else:
        print(f"   Using existing analysis: {analysis.name}")
        print(f"   Status: {analysis.status}")

    # 7. Check if analysis is complete
    if analysis.status != 'completed':
        print("\n7. Analysis Status:")
        print(f"   Status: {analysis.status}")
        print(f"   Progress: {analysis.progress_percentage}%")
        print("\n   ⚠️  Analysis not yet complete!")
        print("   To run the analysis:")
        print("   - Web UI: Visit the analysis page and click 'Process'")
        print("   - API: POST /api/v1/analyses/{id}/process/")
        print("\n   Note: Requires CLIP model to be available")
        return

    print(f"\n7. Analysis complete! ({analysis.images_processed} images processed)")

    # 8. Generate visualizations
    print("\n8. Generating visualizations...")

    # Create output directory
    output_dir = os.path.join(project_root, 'output')
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Generate heatmap
        print("\n   Generating similarity heatmap...")
        heatmap_gen = HeatmapGenerator(analysis)
        heatmap_viz = heatmap_gen.generate_and_save(user=user)
        print(f"   ✓ Saved: {heatmap_viz.file_path}")

        # Generate correlation matrix
        print("\n   Generating correlation matrix...")
        corr_gen = CorrelationMatrixGenerator(analysis)
        corr_viz = corr_gen.generate_and_save(user=user)
        print(f"   ✓ Saved: {corr_viz.file_path}")

        # Generate image grid
        print("\n   Generating image grid...")
        config = {
            'cols': 3,
            'max_images': 12,
            'sort_by': 'score',
            'sort_order': 'desc'
        }
        grid_gen = ImageGridGenerator(analysis, config=config)
        grid_viz = grid_gen.generate_and_save(user=user)
        print(f"   ✓ Saved: {grid_viz.file_path}")

        print("\n✅ Success! Visualizations generated:")
        print(f"   View them at: http://localhost:8000/visualizations/analysis/{analysis.id}/")

    except Exception as e:
        print(f"\n❌ Error generating visualizations: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)
    print(f"\nProject ID: {project.id}")
    print(f"Analysis ID: {analysis.id}")
    print(f"\nNext steps:")
    print(f"  - View in browser: http://localhost:8000/analysis/{project.slug}/{analysis.id}/")
    print(f"  - View visualizations: http://localhost:8000/visualizations/analysis/{analysis.id}/")
    print(f"  - API endpoint: http://localhost:8000/api/v1/analyses/{analysis.id}/")


if __name__ == '__main__':
    main()
