# Django Migration Workplan: CLIP for Humanists

## Executive Summary

This document outlines a comprehensive plan to migrate the **CLIP for Humanists** system from a Google Colab notebook environment to a production-ready Django web application hosted on a VM server. The migration will transform an interactive notebook into a full-featured web platform while maintaining accessibility for non-technical users.

---

## Table of Contents

1. [Current System Analysis](#current-system-analysis)
2. [Target Architecture](#target-architecture)
3. [Migration Phases](#migration-phases)
4. [Detailed Implementation Plan](#detailed-implementation-plan)
5. [Technical Specifications](#technical-specifications)
6. [Security Considerations](#security-considerations)
7. [Testing Strategy](#testing-strategy)
8. [Deployment Plan](#deployment-plan)
9. [Timeline Estimates](#timeline-estimates)
10. [Risk Assessment](#risk-assessment)

---

## Current System Analysis

### Existing Architecture

**Platform:** Google Colab Notebook
**Core Technology:** Python with CLIP (Contrastive Language-Image Pre-training)

### Key Components

1. **Core Modules** (in `src/`)
   - `clip_utils.py` - CLIP model integration and image-text comparison
   - `gps_utils.py` - GPS data extraction from image EXIF data
   - `visualization.py` - Matplotlib/Folium visualization generation
   - `main.py` - ClipForHumanists main orchestration class

2. **Key Features**
   - Image upload and batch processing
   - Text prompt/keyword definition
   - CLIP-based similarity analysis
   - GPS coordinate extraction
   - Multiple visualization types:
     - Similarity heatmaps
     - Interactive maps (Folium)
     - Image grids with scores
     - Correlation matrices
     - Violin plots
     - Location-based analysis
   - Results export (JSON, CSV, ZIP)

3. **Current Dependencies**
   - PyTorch (CLIP model)
   - Transformers (Hugging Face)
   - PIL/Pillow (image processing)
   - Matplotlib (static visualizations)
   - Folium (interactive maps)
   - Pandas (data manipulation)
   - Scikit-learn (clustering, normalization)
   - GeoPy (distance calculations)

### User Workflow (Current)

1. Open Colab notebook
2. Run setup cells
3. Upload images via file widget
4. Define keywords/text prompts
5. Execute processing cells
6. View inline visualizations
7. Download results as ZIP

### Limitations of Current System

- **Session-based:** No persistence between sessions
- **Single-user:** Cannot handle multiple concurrent users
- **No user management:** No accounts, projects, or history
- **Limited scalability:** Colab has resource and time limits
- **No API:** Cannot integrate with other systems
- **Manual process:** Each analysis requires notebook execution
- **No collaboration:** Cannot share projects or results easily
- **Resource constraints:** Colab GPU availability is unpredictable

---

## Target Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer (Nginx)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   Django Application Server                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Web Frontend (Templates/React)             │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │                   Django REST API                       │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │        Business Logic (Views/Serializers/Forms)        │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │          Core Processing Layer (adapted from src/)      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────┬────────────────┬──────────────┬──────────────┘
              │                │              │
    ┌─────────▼──────┐  ┌──────▼──────┐  ┌───▼──────────┐
    │  PostgreSQL DB  │  │ Redis Cache │  │ Celery Queue │
    │   (Metadata)    │  │  (Sessions) │  │ (Async Jobs) │
    └─────────────────┘  └─────────────┘  └───┬──────────┘
                                              │
                                    ┌─────────▼──────────┐
                                    │  Celery Workers    │
                                    │  (GPU Processing)  │
                                    └────────────────────┘
              │
    ┌─────────▼──────────────┐
    │  File Storage          │
    │  - User uploads        │
    │  - Generated results   │
    │  - Visualization cache │
    └────────────────────────┘
```

### Technology Stack

#### Backend
- **Framework:** Django 4.2+ (Python 3.10+)
- **API:** Django REST Framework
- **Task Queue:** Celery with Redis broker
- **Database:** PostgreSQL 14+
- **Cache:** Redis
- **Web Server:** Gunicorn + Nginx
- **File Storage:** Local filesystem or S3-compatible storage

#### Frontend Options
1. **Option A - Django Templates + HTMX** (Recommended for Phase 1)
   - Server-side rendering
   - Progressive enhancement
   - Minimal JavaScript
   - Faster initial development

2. **Option B - React/Vue.js SPA** (Future enhancement)
   - Modern user experience
   - Better interactivity
   - More complex development

#### ML/AI Components
- **CLIP Model:** Same as current (openai/clip-vit-base-patch32)
- **GPU Support:** CUDA-enabled for production, CPU fallback
- **Model Serving:** Loaded in Celery workers, cached in memory

#### DevOps
- **Containerization:** Docker + Docker Compose
- **Process Management:** Supervisor or systemd
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack or Loki
- **Backup:** Automated PostgreSQL backups + file storage sync

---

## Migration Phases

### Phase 1: Foundation (Weeks 1-3)
**Goal:** Set up Django project with basic infrastructure

- Project initialization
- Database design and models
- User authentication system
- Basic file upload functionality
- Development environment setup

### Phase 2: Core Processing (Weeks 4-6)
**Goal:** Migrate CLIP analysis functionality

- Adapt existing `src/` modules for Django
- Implement Celery task queue
- Build asynchronous processing pipeline
- Create job status tracking
- Implement result storage

### Phase 3: Visualization Layer (Weeks 7-9)
**Goal:** Recreate all visualization capabilities

- Migrate visualization functions
- Implement dynamic chart generation
- Create interactive map integration
- Build result browsing interface
- Implement download/export features

### Phase 4: User Features (Weeks 10-12)
**Goal:** Add user-centric features

- Project management
- Analysis history
- Result sharing
- Batch processing interface
- Advanced filtering/search

### Phase 5: Production Ready (Weeks 13-15)
**Goal:** Deployment and optimization

- Performance optimization
- Security hardening
- Comprehensive testing
- Documentation
- Production deployment
- Monitoring setup

### Phase 6: Enhancement (Weeks 16+)
**Goal:** Advanced features and improvements

- API for external integrations
- Collaborative features
- Advanced analytics
- Mobile responsiveness improvements
- Optional: React frontend migration

---

## Detailed Implementation Plan

### 1. Django Project Setup

#### 1.1 Project Structure
```
clip_humanists_web/
├── config/                          # Project configuration
│   ├── settings/
│   │   ├── base.py                 # Base settings
│   │   ├── development.py          # Dev settings
│   │   ├── production.py           # Prod settings
│   │   └── test.py                 # Test settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/                    # User management
│   │   ├── models.py               # User profile, preferences
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── forms.py
│   ├── projects/                    # Project management
│   │   ├── models.py               # Project, Analysis, Dataset
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── forms.py
│   ├── images/                      # Image management
│   │   ├── models.py               # Image, ImageMetadata, GPSData
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── utils.py
│   ├── analysis/                    # CLIP analysis engine
│   │   ├── models.py               # AnalysisJob, TextPrompt, SimilarityResult
│   │   ├── tasks.py                # Celery tasks
│   │   ├── clip_service.py         # Adapted from clip_utils.py
│   │   ├── gps_service.py          # Adapted from gps_utils.py
│   │   └── processors.py           # Analysis orchestration
│   ├── visualizations/              # Visualization generation
│   │   ├── models.py               # Visualization, ChartData
│   │   ├── tasks.py                # Async chart generation
│   │   ├── generators.py           # Adapted from visualization.py
│   │   └── exporters.py            # Export to various formats
│   └── api/                         # REST API
│       ├── v1/
│       │   ├── urls.py
│       │   ├── views.py
│       │   └── permissions.py
│       └── serializers.py
├── core/                            # Shared utilities
│   ├── exceptions.py
│   ├── mixins.py
│   ├── pagination.py
│   └── utils.py
├── static/                          # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── templates/                       # Django templates
│   ├── base.html
│   ├── accounts/
│   ├── projects/
│   ├── analysis/
│   └── visualizations/
├── media/                           # User uploads
│   ├── uploads/
│   ├── results/
│   └── visualizations/
├── tests/                           # Test suite
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   ├── production.txt
│   └── test.txt
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
├── scripts/                         # Management scripts
├── docs/                            # Documentation
└── manage.py
```

#### 1.2 Initial Django Apps

**accounts**
- Custom User model with profile
- Authentication (login, registration, password reset)
- User preferences (email notifications, default settings)
- API tokens for programmatic access

**projects**
- Project model (container for related analyses)
- Project sharing and permissions
- Project templates

**images**
- Image upload and validation
- Metadata extraction
- GPS data storage
- Image preprocessing and thumbnails

**analysis**
- Analysis job creation and tracking
- CLIP processing pipeline
- Text prompt management
- Result storage and retrieval

**visualizations**
- Chart generation
- Interactive map creation
- Export functionality
- Caching strategy

### 2. Database Schema

#### 2.1 Core Models

```python
# accounts/models.py
class User(AbstractUser):
    email = EmailField(unique=True)
    institution = CharField(max_length=255, blank=True)
    research_area = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class UserProfile(models.Model):
    user = OneToOneField(User, on_delete=CASCADE)
    avatar = ImageField(upload_to='avatars/', blank=True)
    bio = TextField(blank=True)
    default_text_prompts = JSONField(default=list)
    notification_preferences = JSONField(default=dict)
    storage_used_bytes = BigIntegerField(default=0)
    storage_limit_bytes = BigIntegerField(default=5*1024**3)  # 5GB

# projects/models.py
class Project(models.Model):
    owner = ForeignKey(User, on_delete=CASCADE, related_name='owned_projects')
    name = CharField(max_length=255)
    description = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    is_public = BooleanField(default=False)
    collaborators = ManyToManyField(User, through='ProjectMembership')
    tags = JSONField(default=list)

class ProjectMembership(models.Model):
    ROLES = [('owner', 'Owner'), ('editor', 'Editor'), ('viewer', 'Viewer')]
    project = ForeignKey(Project, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)
    role = CharField(max_length=20, choices=ROLES)
    joined_at = DateTimeField(auto_now_add=True)

# images/models.py
class ImageDataset(models.Model):
    project = ForeignKey(Project, on_delete=CASCADE, related_name='datasets')
    name = CharField(max_length=255)
    description = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)
    image_count = IntegerField(default=0)

class Image(models.Model):
    dataset = ForeignKey(ImageDataset, on_delete=CASCADE, related_name='images')
    file = ImageField(upload_to='uploads/%Y/%m/%d/')
    original_filename = CharField(max_length=255)
    file_size = IntegerField()
    width = IntegerField()
    height = IntegerField()
    format = CharField(max_length=10)
    uploaded_at = DateTimeField(auto_now_add=True)
    uploaded_by = ForeignKey(User, on_delete=SET_NULL, null=True)

class ImageMetadata(models.Model):
    image = OneToOneField(Image, on_delete=CASCADE, related_name='metadata')
    exif_data = JSONField(default=dict)
    has_gps = BooleanField(default=False)

class GPSData(models.Model):
    image = OneToOneField(Image, on_delete=CASCADE, related_name='gps_data')
    latitude = DecimalField(max_digits=9, decimal_places=6)
    longitude = DecimalField(max_digits=9, decimal_places=6)
    altitude = DecimalField(max_digits=8, decimal_places=2, null=True)
    location_tag = CharField(max_length=255, blank=True)
    normalized_latitude = FloatField(null=True)
    normalized_longitude = FloatField(null=True)
    location_cluster = IntegerField(null=True)

# analysis/models.py
class Analysis(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]

    project = ForeignKey(Project, on_delete=CASCADE, related_name='analyses')
    dataset = ForeignKey(ImageDataset, on_delete=CASCADE)
    name = CharField(max_length=255)
    description = TextField(blank=True)
    status = CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = DateTimeField(auto_now_add=True)
    started_at = DateTimeField(null=True)
    completed_at = DateTimeField(null=True)
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)

    # Processing details
    model_name = CharField(max_length=100, default='openai/clip-vit-base-patch32')
    celery_task_id = CharField(max_length=255, blank=True)
    progress_percentage = IntegerField(default=0)
    error_message = TextField(blank=True)

    # Results summary
    images_processed = IntegerField(default=0)
    total_images = IntegerField(default=0)
    processing_time_seconds = FloatField(null=True)

class TextPrompt(models.Model):
    analysis = ForeignKey(Analysis, on_delete=CASCADE, related_name='text_prompts')
    text = CharField(max_length=500)
    order = IntegerField(default=0)
    created_at = DateTimeField(auto_now_add=True)

class SimilarityResult(models.Model):
    analysis = ForeignKey(Analysis, on_delete=CASCADE, related_name='results')
    image = ForeignKey(Image, on_delete=CASCADE, related_name='similarity_results')
    text_prompt = ForeignKey(TextPrompt, on_delete=CASCADE)
    similarity_score = FloatField()
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('analysis', 'image', 'text_prompt')
        indexes = [
            models.Index(fields=['analysis', 'similarity_score']),
            models.Index(fields=['text_prompt', 'similarity_score']),
        ]

# visualizations/models.py
class Visualization(models.Model):
    VIZ_TYPES = [
        ('heatmap', 'Similarity Heatmap'),
        ('map', 'GPS Map'),
        ('correlation', 'Correlation Matrix'),
        ('violin', 'Violin Plot'),
        ('location_corr', 'Location Correlation'),
        ('image_grid', 'Image Grid'),
        ('bar_chart', 'Bar Chart'),
    ]

    analysis = ForeignKey(Analysis, on_delete=CASCADE, related_name='visualizations')
    viz_type = CharField(max_length=50, choices=VIZ_TYPES)
    title = CharField(max_length=255)
    file_path = CharField(max_length=500)
    config = JSONField(default=dict)  # Stores viz-specific parameters
    created_at = DateTimeField(auto_now_add=True)
    created_by = ForeignKey(User, on_delete=SET_NULL, null=True)

class ExportJob(models.Model):
    EXPORT_FORMATS = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('zip', 'ZIP Archive'),
        ('pdf', 'PDF Report'),
    ]

    analysis = ForeignKey(Analysis, on_delete=CASCADE, related_name='exports')
    format = CharField(max_length=20, choices=EXPORT_FORMATS)
    file_path = CharField(max_length=500)
    created_at = DateTimeField(auto_now_add=True)
    celery_task_id = CharField(max_length=255, blank=True)
```

### 3. Adapting Core Processing Logic

#### 3.1 CLIP Service (from clip_utils.py)

```python
# analysis/clip_service.py

from django.conf import settings
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ClipService:
    """
    Singleton service for CLIP model operations.
    Model is loaded once and reused for efficiency.
    """
    _instance = None
    _model = None
    _processor = None
    _device = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize CLIP model and processor."""
        self._device = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = settings.CLIP_MODEL_NAME

        logger.info(f"Loading CLIP model: {model_name} on device: {self._device}")

        self._model = CLIPModel.from_pretrained(model_name).to(self._device)
        self._processor = CLIPProcessor.from_pretrained(model_name)

        logger.info("CLIP model loaded successfully")

    def compare_image_with_texts(
        self,
        image_path: str,
        text_list: List[str]
    ) -> Dict[str, float]:
        """
        Compare an image with multiple text prompts.

        Args:
            image_path: Path to image file
            text_list: List of text prompts

        Returns:
            Dictionary mapping text prompts to similarity scores
        """
        try:
            # Load and process image
            image = Image.open(image_path)
            image_input = self._processor(
                images=image,
                return_tensors="pt"
            ).to(self._device)

            # Process text
            text_inputs = self._processor(
                text=text_list,
                return_tensors="pt",
                padding=True
            ).to(self._device)

            # Calculate similarities
            with torch.no_grad():
                image_features = self._model.get_image_features(**image_input)
                text_features = self._model.get_text_features(**text_inputs)

                # Normalize
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)

                # Calculate similarities
                similarities = (
                    (image_features @ text_features.T).squeeze().cpu().numpy()
                )

            # Format results
            if isinstance(similarities, np.ndarray):
                if similarities.ndim == 0:
                    return {text_list[0]: float(similarities)}
                else:
                    return {
                        text: float(score)
                        for text, score in zip(text_list, similarities)
                    }
            else:
                if len(text_list) == 1:
                    return {text_list[0]: float(similarities)}
                else:
                    return {
                        text: float(score)
                        for text, score in zip(text_list, similarities)
                    }

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return {text: 0.0 for text in text_list}

    def batch_process_images(
        self,
        image_paths: List[str],
        text_list: List[str],
        progress_callback=None
    ) -> List[Dict]:
        """
        Process multiple images in batch.

        Args:
            image_paths: List of image file paths
            text_list: List of text prompts
            progress_callback: Optional callback function for progress updates

        Returns:
            List of results dictionaries
        """
        results = []
        total = len(image_paths)

        for idx, img_path in enumerate(image_paths):
            similarities = self.compare_image_with_texts(img_path, text_list)
            results.append({
                'filepath': img_path,
                'similarities': similarities
            })

            if progress_callback:
                progress_callback(idx + 1, total)

        return results
```

#### 3.2 Celery Tasks (Asynchronous Processing)

```python
# analysis/tasks.py

from celery import shared_task, current_task
from django.conf import settings
from django.utils import timezone
from .models import Analysis, SimilarityResult, TextPrompt
from images.models import Image
from .clip_service import ClipService
from .gps_service import GPSService
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_analysis_job(self, analysis_id: int):
    """
    Main task for processing an analysis job.

    Args:
        analysis_id: ID of the Analysis object
    """
    try:
        # Get analysis object
        analysis = Analysis.objects.get(id=analysis_id)
        analysis.status = 'processing'
        analysis.started_at = timezone.now()
        analysis.celery_task_id = self.request.id
        analysis.save()

        # Get images and text prompts
        images = analysis.dataset.images.all()
        text_prompts = analysis.text_prompts.all().order_by('order')
        text_list = [prompt.text for prompt in text_prompts]

        total_images = images.count()
        analysis.total_images = total_images
        analysis.save()

        # Initialize CLIP service
        clip_service = ClipService()

        # Process each image
        for idx, image in enumerate(images):
            # Update progress
            progress = int((idx / total_images) * 100)
            analysis.progress_percentage = progress
            analysis.save()

            # Update task state
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': idx,
                    'total': total_images,
                    'percentage': progress
                }
            )

            # Process image
            try:
                similarities = clip_service.compare_image_with_texts(
                    image.file.path,
                    text_list
                )

                # Save results
                for text_prompt in text_prompts:
                    score = similarities.get(text_prompt.text, 0.0)
                    SimilarityResult.objects.create(
                        analysis=analysis,
                        image=image,
                        text_prompt=text_prompt,
                        similarity_score=score
                    )

                analysis.images_processed = idx + 1
                analysis.save()

            except Exception as e:
                logger.error(f"Error processing image {image.id}: {e}")
                continue

        # Calculate processing time
        analysis.completed_at = timezone.now()
        analysis.processing_time_seconds = (
            analysis.completed_at - analysis.started_at
        ).total_seconds()
        analysis.status = 'completed'
        analysis.progress_percentage = 100
        analysis.save()

        # Trigger post-processing tasks
        post_process_analysis.delay(analysis_id)

        return {
            'status': 'completed',
            'images_processed': analysis.images_processed,
            'processing_time': analysis.processing_time_seconds
        }

    except Analysis.DoesNotExist:
        logger.error(f"Analysis {analysis_id} not found")
        raise

    except Exception as e:
        logger.error(f"Error processing analysis {analysis_id}: {e}")
        analysis.status = 'failed'
        analysis.error_message = str(e)
        analysis.save()
        raise self.retry(exc=e, countdown=60)

@shared_task
def post_process_analysis(analysis_id: int):
    """
    Post-processing tasks after analysis completes.
    - Extract GPS data
    - Normalize coordinates
    - Cluster locations
    - Generate default visualizations
    """
    try:
        analysis = Analysis.objects.get(id=analysis_id)
        gps_service = GPSService()

        # Extract and process GPS data
        images_with_gps = analysis.dataset.images.filter(
            metadata__has_gps=True
        )

        if images_with_gps.exists():
            gps_service.normalize_coordinates(images_with_gps)
            gps_service.cluster_locations(images_with_gps)

        # Generate default visualizations
        from visualizations.tasks import generate_default_visualizations
        generate_default_visualizations.delay(analysis_id)

    except Exception as e:
        logger.error(f"Error in post-processing for analysis {analysis_id}: {e}")

@shared_task(bind=True)
def extract_image_metadata(self, image_id: int):
    """
    Extract metadata from an uploaded image.
    """
    try:
        from images.utils import extract_image_metadata as extract_meta
        image = Image.objects.get(id=image_id)
        extract_meta(image)
    except Exception as e:
        logger.error(f"Error extracting metadata for image {image_id}: {e}")
        raise
```

### 4. Views and API Endpoints

#### 4.1 Key Views

```python
# projects/views.py

from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import Project, Analysis
from .forms import ProjectForm, AnalysisForm

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(
            owner=self.request.user
        ) | Project.objects.filter(
            collaborators=self.request.user
        ).distinct()

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'

    def get_queryset(self):
        return Project.objects.filter(
            owner=self.request.user
        ) | Project.objects.filter(
            collaborators=self.request.user
        )

class AnalysisCreateView(LoginRequiredMixin, CreateView):
    model = Analysis
    form_class = AnalysisForm
    template_name = 'analysis/create_analysis.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        # Trigger Celery task
        from analysis.tasks import process_analysis_job
        process_analysis_job.delay(self.object.id)

        return response
```

#### 4.2 REST API

```python
# api/v1/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from projects.models import Project, Analysis
from api.serializers import ProjectSerializer, AnalysisSerializer
from analysis.tasks import process_analysis_job

class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Project.objects.filter(
            owner=self.request.user
        ) | Project.objects.filter(
            collaborators=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        project_id = self.request.query_params.get('project_id')
        if project_id:
            return Analysis.objects.filter(project_id=project_id)
        return Analysis.objects.filter(
            project__owner=self.request.user
        ) | Analysis.objects.filter(
            project__collaborators=self.request.user
        ).distinct()

    @action(detail=True, methods=['post'])
    def start_processing(self, request, pk=None):
        """Start processing an analysis job."""
        analysis = self.get_object()

        if analysis.status != 'pending':
            return Response(
                {'error': 'Analysis already started'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Trigger Celery task
        task = process_analysis_job.delay(analysis.id)

        return Response({
            'status': 'processing',
            'task_id': task.id
        })

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get processing progress."""
        analysis = self.get_object()

        return Response({
            'status': analysis.status,
            'progress_percentage': analysis.progress_percentage,
            'images_processed': analysis.images_processed,
            'total_images': analysis.total_images
        })

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get analysis results."""
        analysis = self.get_object()

        if analysis.status != 'completed':
            return Response(
                {'error': 'Analysis not completed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )

        results = analysis.results.select_related(
            'image', 'text_prompt'
        ).all()

        # Format results
        data = []
        for result in results:
            data.append({
                'image_id': result.image.id,
                'image_filename': result.image.original_filename,
                'text_prompt': result.text_prompt.text,
                'similarity_score': result.similarity_score
            })

        return Response({'results': data})
```

### 5. Frontend Templates (HTMX Approach)

#### 5.1 Base Template

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}CLIP for Humanists{% endblock %}</title>

    <!-- CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{% static 'css/main.css' %}">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{% url 'home' %}">CLIP for Humanists</a>
            <div class="navbar-nav ms-auto">
                {% if user.is_authenticated %}
                    <a class="nav-link" href="{% url 'projects:list' %}">Projects</a>
                    <a class="nav-link" href="{% url 'accounts:profile' %}">Profile</a>
                    <a class="nav-link" href="{% url 'logout' %}">Logout</a>
                {% else %}
                    <a class="nav-link" href="{% url 'login' %}">Login</a>
                    <a class="nav-link" href="{% url 'register' %}">Register</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <main class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}{% endblock %}
    </main>

    <!-- JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### 5.2 Analysis Creation Form

```html
<!-- templates/analysis/create_analysis.html -->
{% extends 'base.html' %}

{% block content %}
<div class="row">
    <div class="col-md-8 offset-md-2">
        <h1>Create New Analysis</h1>

        <form method="post" enctype="multipart/form-data" id="analysis-form">
            {% csrf_token %}

            <div class="mb-3">
                <label for="name" class="form-label">Analysis Name</label>
                <input type="text" class="form-control" name="name" required>
            </div>

            <div class="mb-3">
                <label for="description" class="form-label">Description</label>
                <textarea class="form-control" name="description" rows="3"></textarea>
            </div>

            <div class="mb-3">
                <label class="form-label">Upload Images</label>
                <input type="file" class="form-control" name="images" multiple accept="image/*" required>
                <small class="form-text text-muted">
                    Select one or more images (JPEG, PNG). Maximum 100 images per analysis.
                </small>
            </div>

            <div class="mb-3">
                <label class="form-label">Text Prompts / Keywords</label>
                <div id="prompts-container">
                    <div class="input-group mb-2">
                        <input type="text" class="form-control" name="prompts[]"
                               placeholder="Enter a keyword or phrase" required>
                        <button class="btn btn-outline-danger" type="button"
                                onclick="removePrompt(this)">Remove</button>
                    </div>
                </div>
                <button type="button" class="btn btn-sm btn-secondary" onclick="addPrompt()">
                    + Add Another Prompt
                </button>
            </div>

            <button type="submit" class="btn btn-primary">Start Analysis</button>
            <a href="{% url 'projects:detail' project.id %}" class="btn btn-secondary">Cancel</a>
        </form>
    </div>
</div>

<script>
function addPrompt() {
    const container = document.getElementById('prompts-container');
    const div = document.createElement('div');
    div.className = 'input-group mb-2';
    div.innerHTML = `
        <input type="text" class="form-control" name="prompts[]"
               placeholder="Enter a keyword or phrase" required>
        <button class="btn btn-outline-danger" type="button"
                onclick="removePrompt(this)">Remove</button>
    `;
    container.appendChild(div);
}

function removePrompt(btn) {
    const container = document.getElementById('prompts-container');
    if (container.children.length > 1) {
        btn.parentElement.remove();
    }
}
</script>
{% endblock %}
```

#### 5.3 Analysis Results View with HTMX

```html
<!-- templates/analysis/results.html -->
{% extends 'base.html' %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1>{{ analysis.name }}</h1>
        <p class="text-muted">{{ analysis.description }}</p>

        <div class="card mb-4">
            <div class="card-body">
                <h5>Analysis Status</h5>
                <div hx-get="{% url 'api:analysis-progress' analysis.id %}"
                     hx-trigger="every 2s"
                     hx-swap="innerHTML">
                    <div class="progress">
                        <div class="progress-bar" role="progressbar"
                             style="width: {{ analysis.progress_percentage }}%">
                            {{ analysis.progress_percentage }}%
                        </div>
                    </div>
                    <p class="mt-2">
                        Status: <strong>{{ analysis.status }}</strong> |
                        Processed: {{ analysis.images_processed }}/{{ analysis.total_images }}
                    </p>
                </div>
            </div>
        </div>

        {% if analysis.status == 'completed' %}
        <div class="card mb-4">
            <div class="card-body">
                <h5>Visualizations</h5>
                <div class="row">
                    {% for viz in analysis.visualizations.all %}
                    <div class="col-md-4 mb-3">
                        <div class="card">
                            <img src="{{ viz.file_path }}" class="card-img-top" alt="{{ viz.title }}">
                            <div class="card-body">
                                <h6 class="card-title">{{ viz.title }}</h6>
                                <a href="{{ viz.file_path }}" download class="btn btn-sm btn-primary">
                                    Download
                                </a>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-body">
                <h5>Results</h5>
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Image</th>
                                {% for prompt in analysis.text_prompts.all %}
                                <th>{{ prompt.text }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for image in analysis.dataset.images.all %}
                            <tr>
                                <td>
                                    <img src="{{ image.file.url }}" alt="{{ image.original_filename }}"
                                         style="max-width: 100px;">
                                    <br>{{ image.original_filename }}
                                </td>
                                {% for prompt in analysis.text_prompts.all %}
                                <td>
                                    {% with result=image.similarity_results.filter(analysis=analysis,text_prompt=prompt).first %}
                                        {{ result.similarity_score|floatformat:3 }}
                                    {% endwith %}
                                </td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <a href="{% url 'api:analysis-export' analysis.id %}?format=csv"
                   class="btn btn-success">Export as CSV</a>
                <a href="{% url 'api:analysis-export' analysis.id %}?format=json"
                   class="btn btn-info">Export as JSON</a>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}
```

### 6. Configuration

#### 6.1 Settings Structure

```python
# config/settings/base.py

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# CLIP Configuration
CLIP_MODEL_NAME = os.getenv('CLIP_MODEL_NAME', 'openai/clip-vit-base-patch32')
CLIP_DEVICE = os.getenv('CLIP_DEVICE', 'auto')  # 'auto', 'cuda', or 'cpu'

# File Upload Configuration
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB per image
MAX_IMAGES_PER_ANALYSIS = 100
ALLOWED_IMAGE_FORMATS = ['JPEG', 'PNG', 'JPG']

# Storage Configuration
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
    }
}

# Database
# Will be overridden in production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'clip_humanists'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

#### 6.2 Docker Configuration

```dockerfile
# docker/Dockerfile

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements/production.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create directories
RUN mkdir -p /app/media /app/static /app/logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Run as non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

```yaml
# docker/docker-compose.yml

version: '3.8'

services:
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: clip_humanists
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - ../media:/app/media
      - ../logs:/app/logs
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/clip_humanists
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery_worker:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    command: celery -A config worker -l info --concurrency=2
    volumes:
      - ../media:/app/media
      - ../logs:/app/logs
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/clip_humanists
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - db
      - redis

  celery_beat:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    command: celery -A config beat -l info
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/clip_humanists
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ../media:/app/media:ro
      - ../static:/app/static:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
```

---

## Technical Specifications

### Performance Requirements

- **Response Time:**
  - Page load: < 2 seconds
  - Analysis start: < 1 second
  - Progress updates: Real-time (2-second polling)

- **Throughput:**
  - Support 50+ concurrent users
  - Process 100 images in < 10 minutes (with GPU)
  - Handle 1000+ images per analysis (batched processing)

- **Storage:**
  - 5GB per user default quota
  - Automatic cleanup of old results (configurable retention)
  - Efficient thumbnail generation

### Scalability Strategy

1. **Horizontal Scaling:**
   - Stateless Django app servers
   - Multiple Celery workers
   - Load balancer (Nginx)

2. **Vertical Scaling:**
   - GPU-enabled workers for CLIP processing
   - Database connection pooling
   - Redis caching

3. **Resource Optimization:**
   - Lazy model loading
   - Result pagination
   - Image compression and thumbnails
   - CDN for static assets (future)

---

## Security Considerations

### Authentication & Authorization

- **User Authentication:**
  - Django's built-in authentication
  - Password complexity requirements
  - Optional: OAuth2 integration (Google, ORCID)
  - Two-factor authentication (future)

- **Authorization:**
  - Row-level permissions
  - Project-based access control
  - API token management
  - Rate limiting

### Data Security

- **In Transit:**
  - HTTPS/TLS encryption
  - Secure WebSocket connections (for real-time updates)

- **At Rest:**
  - Encrypted database fields for sensitive data
  - Secure file storage permissions
  - Regular backups with encryption

### Input Validation

- **File Upload Security:**
  - MIME type verification
  - File size limits
  - Virus scanning (ClamAV integration)
  - Sanitized filenames

- **SQL Injection Prevention:**
  - Django ORM (parameterized queries)
  - No raw SQL without sanitization

- **XSS Prevention:**
  - Template auto-escaping
  - CSP headers
  - Input sanitization

### Infrastructure Security

- **Firewall Configuration:**
  - Whitelist necessary ports only
  - VPC isolation (if cloud-hosted)

- **Dependency Management:**
  - Regular security updates
  - Vulnerability scanning (Snyk, Safety)
  - Minimal container images

---

## Testing Strategy

### Test Pyramid

```
         /\
        /E2E\      (5% - End-to-end tests)
       /------\
      /Integ.  \   (15% - Integration tests)
     /----------\
    /   Unit     \ (80% - Unit tests)
   /--------------\
```

### Test Coverage

1. **Unit Tests (80%):**
   - Model methods
   - Utility functions
   - Service classes
   - Form validation

2. **Integration Tests (15%):**
   - API endpoints
   - Celery tasks
   - Database operations
   - File processing

3. **End-to-End Tests (5%):**
   - Critical user flows
   - Analysis creation workflow
   - Result visualization
   - Export functionality

### Testing Tools

- **pytest** - Test framework
- **pytest-django** - Django integration
- **factory_boy** - Test data factories
- **Faker** - Realistic test data
- **pytest-cov** - Coverage reporting
- **Selenium/Playwright** - E2E tests

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml

name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements/test.txt

      - name: Run tests
        run: |
          pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Deployment Plan

### Deployment Environments

1. **Development:**
   - Local Docker Compose
   - Debug mode enabled
   - SQLite or local PostgreSQL

2. **Staging:**
   - VM mirror of production
   - Production-like data
   - Testing ground for releases

3. **Production:**
   - VM with proper resources
   - Nginx + Gunicorn
   - PostgreSQL + Redis
   - Celery workers with GPU

### Deployment Checklist

**Pre-Deployment:**
- [ ] Run full test suite
- [ ] Update documentation
- [ ] Database migration plan
- [ ] Backup current system
- [ ] Review security settings

**Deployment:**
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Database migrations
- [ ] Collect static files
- [ ] Restart services
- [ ] Verify Celery workers

**Post-Deployment:**
- [ ] Monitor logs
- [ ] Check error rates
- [ ] Verify key workflows
- [ ] Performance monitoring
- [ ] User communication

### Rollback Plan

1. Keep previous Docker images
2. Database backup before migration
3. Quick rollback script:
   ```bash
   ./scripts/rollback.sh <previous_version>
   ```

---

## Timeline Estimates

### Phase 1: Foundation (3 weeks)
- Week 1: Project setup, database design
- Week 2: User auth, basic models
- Week 3: File upload, basic views

### Phase 2: Core Processing (3 weeks)
- Week 4: Adapt CLIP service
- Week 5: Celery integration
- Week 6: Job tracking, result storage

### Phase 3: Visualization (3 weeks)
- Week 7: Chart generation
- Week 8: Interactive maps
- Week 9: Export functionality

### Phase 4: User Features (3 weeks)
- Week 10: Project management
- Week 11: Analysis history
- Week 12: Sharing features

### Phase 5: Production Ready (3 weeks)
- Week 13: Testing, optimization
- Week 14: Documentation, security
- Week 15: Deployment, monitoring

### Phase 6: Enhancement (Ongoing)
- API development
- Advanced features
- User feedback iteration

**Total Estimated Time:** 15 weeks (3.5 months) for MVP

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| GPU availability issues | Medium | High | CPU fallback, queue prioritization |
| Model loading performance | Medium | Medium | Model caching, singleton pattern |
| Large file processing timeout | Medium | Medium | Chunked processing, progress tracking |
| Database performance at scale | Low | High | Indexing, query optimization, caching |
| Storage limitations | Medium | Medium | Quota management, cleanup policies |

### Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | High | Medium | Clear requirements, phase-based delivery |
| Timeline delays | Medium | Medium | Buffer time, MVP focus |
| Resource constraints | Medium | High | Cloud bursting, scalable architecture |
| User adoption issues | Low | Medium | User testing, documentation, training |

---

## Success Metrics

### Technical Metrics
- 99% uptime
- < 2s average page load time
- < 10min processing time for 100 images
- < 1% error rate

### User Metrics
- 100+ active users in first 3 months
- 500+ analyses completed
- 80%+ user satisfaction
- < 5% support ticket rate

### Business Metrics
- Cost per analysis < $0.50
- Server utilization 40-70%
- Storage growth < 100GB/month

---

## Appendix

### A. Migration from Colab Notebook Mapping

| Notebook Feature | Django Equivalent |
|------------------|-------------------|
| Cell execution | View/API endpoint |
| File upload widget | Django Form + Ajax upload |
| Inline visualizations | Rendered templates + charts |
| Progress updates | Celery + WebSocket/Polling |
| Results download | Export views |
| Session state | Database + user authentication |

### B. Key Dependencies

```
# requirements/base.txt
Django==4.2.7
djangorestframework==3.14.0
celery==5.3.4
redis==5.0.1
psycopg2-binary==2.9.9
Pillow==10.1.0
torch==2.1.0
transformers==4.35.0
matplotlib==3.8.1
folium==0.15.0
pandas==2.1.3
numpy==1.26.2
scikit-learn==1.3.2
scipy==1.11.4
geopy==2.4.1
gunicorn==21.2.0
```

### C. Environment Variables

```bash
# .env.example
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_NAME=clip_humanists
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

CLIP_MODEL_NAME=openai/clip-vit-base-patch32
CLIP_DEVICE=auto

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

SENTRY_DSN=your-sentry-dsn  # Optional
```

---

## Conclusion

This workplan provides a comprehensive roadmap for migrating CLIP for Humanists from a Colab notebook to a production Django web application. The phased approach ensures systematic development while maintaining the tool's accessibility for non-technical users.

**Key Success Factors:**
1. Maintain feature parity with notebook version
2. Improve user experience through web interface
3. Enable multi-user collaboration
4. Ensure scalability and performance
5. Prioritize security and data privacy

**Next Steps:**
1. Review and approve this workplan
2. Set up development environment
3. Begin Phase 1 implementation
4. Establish regular check-ins and progress reviews

---

**Document Version:** 1.0
**Last Updated:** 2025-11-04
**Author:** Claude Code Assistant
