"""
API Views for CLIP for Humanists.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404

from apps.projects.models import Project, ProjectMembership
from apps.images.models import ImageDataset, Image
from apps.analysis.models import Analysis, TextPrompt, SimilarityResult
from apps.visualizations.models import Visualization, ExportJob
from apps.analysis.tasks import process_analysis_job
from apps.visualizations.tasks import export_analysis_results

from .serializers import (
    ProjectListSerializer, ProjectDetailSerializer,
    ImageDatasetListSerializer, ImageDatasetDetailSerializer,
    ImageListSerializer, ImageDetailSerializer,
    AnalysisListSerializer, AnalysisDetailSerializer,
    AnalysisCreateSerializer, SimilarityResultSerializer,
    VisualizationSerializer, ExportJobSerializer,
    TextPromptSerializer, ImageSearchResultSerializer,
    AnalysisStatisticsSerializer
)
from .permissions import IsOwnerOrCollaborator, IsProjectMember


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project model.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'name']
    ordering = ['-updated_at']
    filterset_fields = ['is_public']

    def get_queryset(self):
        """Return projects user owns or collaborates on."""
        user = self.request.user
        return Project.objects.filter(
            Q(owner=user) | Q(collaborators=user)
        ).distinct()

    def get_serializer_class(self):
        """Use different serializers for list vs detail."""
        if self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer

    def perform_create(self, serializer):
        """Set the owner to current user."""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def add_collaborator(self, request, pk=None):
        """Add a collaborator to the project."""
        project = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'viewer')

        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already a collaborator
        if ProjectMembership.objects.filter(project=project, user_id=user_id).exists():
            return Response(
                {'error': 'User is already a collaborator'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create membership
        ProjectMembership.objects.create(
            project=project,
            user_id=user_id,
            role=role,
            invited_by=request.user
        )

        return Response({'status': 'collaborator added'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_collaborator(self, request, pk=None):
        """Remove a collaborator from the project."""
        project = self.get_object()
        user_id = request.data.get('user_id')

        membership = get_object_or_404(
            ProjectMembership,
            project=project,
            user_id=user_id
        )
        membership.delete()

        return Response({'status': 'collaborator removed'})


class ImageDatasetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ImageDataset model.
    """
    permission_classes = [IsAuthenticated, IsProjectMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return datasets from user's projects."""
        user = self.request.user
        return ImageDataset.objects.filter(
            project__in=Project.objects.filter(
                Q(owner=user) | Q(collaborators=user)
            )
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return ImageDatasetListSerializer
        return ImageDatasetDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Image model.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['original_filename']
    ordering_fields = ['uploaded_at', 'original_filename', 'file_size']
    ordering = ['-uploaded_at']
    filterset_fields = ['format', 'dataset']

    def get_queryset(self):
        """Return images from user's datasets."""
        user = self.request.user
        return Image.objects.filter(
            dataset__project__in=Project.objects.filter(
                Q(owner=user) | Q(collaborators=user)
            )
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'list':
            return ImageListSerializer
        return ImageDetailSerializer

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        Semantic search for images using CLIP.
        """
        query = request.data.get('query', '')
        project_id = request.data.get('project_id')
        dataset_id = request.data.get('dataset_id')
        threshold = float(request.data.get('threshold', 0.5))

        if not query:
            return Response(
                {'error': 'query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build queryset based on filters
        queryset = self.get_queryset()
        if project_id:
            queryset = queryset.filter(dataset__project_id=project_id)
        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)

        # Perform semantic search using CLIP
        from apps.analysis.clip_service import get_clip_service
        clip_service = get_clip_service()

        results = []
        for image in queryset:
            # Calculate similarity
            similarities = clip_service.compare_image_with_texts(
                image.file.path,
                [query]
            )
            score = similarities.get(query, 0.0)

            if score >= threshold:
                results.append({
                    'image': image,
                    'similarity_score': score,
                    'matched_concepts': [query]
                })

        # Sort by score
        results.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Serialize
        serializer = ImageSearchResultSerializer(results, many=True)
        return Response(serializer.data)


class AnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Analysis model.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    filterset_fields = ['status', 'project']

    def get_queryset(self):
        """Return analyses from user's projects."""
        user = self.request.user
        return Analysis.objects.filter(
            project__in=Project.objects.filter(
                Q(owner=user) | Q(collaborators=user)
            )
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'create':
            return AnalysisCreateSerializer
        elif self.action == 'list':
            return AnalysisListSerializer
        return AnalysisDetailSerializer

    def perform_create(self, serializer):
        """Create analysis and trigger processing."""
        analysis = serializer.save(created_by=self.request.user)

        # Trigger Celery task
        process_analysis_job.delay(analysis.id)

        return analysis

    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get analysis progress."""
        analysis = self.get_object()
        return Response({
            'status': analysis.status,
            'progress_percentage': analysis.progress_percentage,
            'images_processed': analysis.images_processed,
            'total_images': analysis.total_images,
            'progress_display': analysis.get_progress_display()
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

        # Get results with pagination
        results = analysis.results.select_related('image', 'text_prompt').all()

        # Apply filters if provided
        text_prompt = request.query_params.get('text_prompt')
        if text_prompt:
            results = results.filter(text_prompt__text=text_prompt)

        min_score = request.query_params.get('min_score')
        if min_score:
            results = results.filter(similarity_score__gte=float(min_score))

        # Paginate
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = SimilarityResultSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = SimilarityResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistical summary of analysis results."""
        analysis = self.get_object()

        if analysis.status != 'completed':
            return Response(
                {'error': 'Analysis not completed yet'},
                status=status.HTTP_400_BAD_REQUEST
            )

        stats = []
        for prompt in analysis.text_prompts.all():
            scores = analysis.results.filter(text_prompt=prompt).values_list(
                'similarity_score', flat=True
            )
            if scores:
                import numpy as np
                stats.append({
                    'concept': prompt.text,
                    'mean_score': float(np.mean(scores)),
                    'median_score': float(np.median(scores)),
                    'std_dev': float(np.std(scores)),
                    'min_score': float(np.min(scores)),
                    'max_score': float(np.max(scores)),
                    'count': len(scores)
                })

        serializer = AnalysisStatisticsSerializer(stats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """Create an export job for the analysis."""
        analysis = self.get_object()
        export_format = request.data.get('format', 'csv')
        include_images = request.data.get('include_images', False)
        include_visualizations = request.data.get('include_visualizations', True)

        # Create export job
        export_job = ExportJob.objects.create(
            analysis=analysis,
            format=export_format,
            include_images=include_images,
            include_visualizations=include_visualizations,
            created_by=request.user
        )

        # Trigger export task
        export_analysis_results.delay(export_job.id)

        serializer = ExportJobSerializer(export_job)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VisualizationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Visualization model (read-only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = VisualizationSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'viz_type']
    ordering = ['-created_at']
    filterset_fields = ['viz_type', 'analysis']

    def get_queryset(self):
        """Return visualizations from user's analyses."""
        user = self.request.user
        return Visualization.objects.filter(
            analysis__project__in=Project.objects.filter(
                Q(owner=user) | Q(collaborators=user)
            )
        ).distinct()


class ExportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for ExportJob model (read-only).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ExportJobSerializer
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    filterset_fields = ['status', 'format', 'analysis']

    def get_queryset(self):
        """Return export jobs from user's analyses."""
        user = self.request.user
        return ExportJob.objects.filter(
            analysis__project__in=Project.objects.filter(
                Q(owner=user) | Q(collaborators=user)
            )
        ).distinct()

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get export job status."""
        export_job = self.get_object()
        return Response({
            'status': export_job.status,
            'file_url': export_job.get_file_url(),
            'error_message': export_job.error_message
        })
