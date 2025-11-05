"""
Views for visualization management and display.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
import logging

from .models import Visualization
from apps.analysis.models import Analysis
from .tasks import generate_default_visualizations, generate_custom_visualization

logger = logging.getLogger(__name__)


class VisualizationGalleryView(LoginRequiredMixin, ListView):
    """
    Display all visualizations for a specific analysis.
    """
    model = Visualization
    template_name = 'visualizations/visualization_gallery.html'
    context_object_name = 'visualizations'
    paginate_by = 24

    def get_queryset(self):
        """Get visualizations for the specified analysis."""
        analysis_id = self.kwargs.get('analysis_id')
        self.analysis = get_object_or_404(Analysis, id=analysis_id)

        # Check permissions
        project = self.analysis.dataset.project
        if not (project.is_public or
                project.owner == self.request.user or
                self.request.user in project.collaborators.all()):
            return Visualization.objects.none()

        return Visualization.objects.filter(
            analysis=self.analysis
        ).select_related(
            'analysis',
            'analysis__dataset',
            'analysis__dataset__project',
            'created_by'
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        """Add analysis and permission info to context."""
        context = super().get_context_data(**kwargs)
        context['analysis'] = self.analysis

        # Check if user can edit (owner or collaborator)
        project = self.analysis.dataset.project
        context['can_edit'] = (
            project.owner == self.request.user or
            self.request.user in project.collaborators.all()
        )

        return context


class VisualizationDetailView(LoginRequiredMixin, DetailView):
    """
    Display a single visualization with controls.
    """
    model = Visualization
    template_name = 'visualizations/visualization_detail.html'
    context_object_name = 'visualization'
    pk_url_kwarg = 'viz_id'

    def get_queryset(self):
        """Filter by permissions."""
        return Visualization.objects.select_related(
            'analysis',
            'analysis__dataset',
            'analysis__dataset__project',
            'created_by'
        )

    def get_object(self, queryset=None):
        """Get visualization and check permissions."""
        obj = super().get_object(queryset)

        # Check if user has access to this visualization
        project = obj.analysis.dataset.project
        if not (project.is_public or
                project.owner == self.request.user or
                self.request.user in project.collaborators.all()):
            raise PermissionError("You don't have permission to view this visualization")

        return obj

    def get_context_data(self, **kwargs):
        """Add permission info to context."""
        context = super().get_context_data(**kwargs)

        # Check if user can edit
        project = self.object.analysis.dataset.project
        context['can_edit'] = (
            project.owner == self.request.user or
            self.request.user in project.collaborators.all()
        )

        return context


class VisualizationListView(LoginRequiredMixin, ListView):
    """
    Browse all visualizations with filtering.
    """
    model = Visualization
    template_name = 'visualizations/visualization_list.html'
    context_object_name = 'visualizations'
    paginate_by = 20

    def get_queryset(self):
        """Get all visualizations user has access to, with optional filtering."""
        # Base queryset - visualizations from accessible projects
        qs = Visualization.objects.filter(
            Q(analysis__dataset__project__owner=self.request.user) |
            Q(analysis__dataset__project__collaborators=self.request.user) |
            Q(analysis__dataset__project__is_public=True)
        ).select_related(
            'analysis',
            'analysis__dataset',
            'analysis__dataset__project',
            'created_by'
        ).distinct()

        # Apply filters
        viz_type = self.request.GET.get('viz_type')
        if viz_type:
            qs = qs.filter(viz_type=viz_type)

        file_format = self.request.GET.get('format')
        if file_format:
            qs = qs.filter(file_format=file_format)

        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(analysis__name__icontains=search)
            )

        # Ordering
        qs = qs.order_by('-created_at')

        return qs

    def get_context_data(self, **kwargs):
        """Add view mode to context."""
        context = super().get_context_data(**kwargs)
        context['view'] = self.request.GET.get('view', 'table')
        return context


class GenerateVisualizationView(LoginRequiredMixin, View):
    """
    Handle visualization generation requests.
    """

    def post(self, request, analysis_id):
        """Generate visualizations for an analysis."""
        analysis = get_object_or_404(Analysis, id=analysis_id)

        # Check permissions
        project = analysis.dataset.project
        if not (project.owner == request.user or
                request.user in project.collaborators.all()):
            return HttpResponseForbidden("You don't have permission to generate visualizations")

        # Get selected visualization types
        viz_types = request.POST.getlist('viz_types')
        async_generation = request.POST.get('async_generation') == 'on'

        if not viz_types:
            messages.error(request, "Please select at least one visualization type.")
            return redirect('visualizations:gallery', analysis_id=analysis_id)

        try:
            if async_generation:
                # Generate asynchronously with Celery
                if len(viz_types) == 3 and set(viz_types) == {'heatmap', 'correlation', 'image_grid'}:
                    # Use default task if all three selected
                    task = generate_default_visualizations.delay(
                        analysis_id=analysis.id,
                        user_id=request.user.id
                    )
                    messages.success(
                        request,
                        f"Generating {len(viz_types)} visualizations in the background. "
                        f"Task ID: {task.id}"
                    )
                else:
                    # Generate each type separately
                    task_ids = []
                    for viz_type in viz_types:
                        task = generate_custom_visualization.delay(
                            analysis_id=analysis.id,
                            viz_type=viz_type,
                            user_id=request.user.id
                        )
                        task_ids.append(task.id)

                    messages.success(
                        request,
                        f"Generating {len(viz_types)} visualizations in the background. "
                        f"Refresh the page in a few moments to see results."
                    )
            else:
                # Generate synchronously (blocks until complete)
                from .generators import (
                    HeatmapGenerator,
                    CorrelationMatrixGenerator,
                    ImageGridGenerator
                )

                generator_map = {
                    'heatmap': HeatmapGenerator,
                    'correlation': CorrelationMatrixGenerator,
                    'image_grid': ImageGridGenerator,
                }

                created_count = 0
                for viz_type in viz_types:
                    generator_class = generator_map.get(viz_type)
                    if generator_class:
                        try:
                            # Add default config for image_grid
                            config = {}
                            if viz_type == 'image_grid':
                                config = {
                                    'cols': 3,
                                    'max_images': 12,
                                    'sort_by': 'score',
                                    'sort_order': 'desc'
                                }

                            generator = generator_class(analysis, config=config)
                            visualization = generator.generate_and_save(user=request.user)
                            created_count += 1
                            logger.info(f"Created {viz_type} visualization {visualization.id}")
                        except Exception as e:
                            logger.error(f"Error generating {viz_type}: {e}", exc_info=True)
                            messages.warning(request, f"Failed to generate {viz_type}: {str(e)}")

                if created_count > 0:
                    messages.success(
                        request,
                        f"Successfully generated {created_count} visualization(s)!"
                    )
                else:
                    messages.error(request, "Failed to generate any visualizations.")

        except Exception as e:
            logger.error(f"Error in visualization generation: {e}", exc_info=True)
            messages.error(request, f"Error generating visualizations: {str(e)}")

        return redirect('visualizations:gallery', analysis_id=analysis_id)


class DeleteVisualizationView(LoginRequiredMixin, DeleteView):
    """
    Delete a visualization with permission checks.
    """
    model = Visualization
    pk_url_kwarg = 'viz_id'

    def get_success_url(self):
        """Redirect back to gallery."""
        return reverse('visualizations:gallery',
                      kwargs={'analysis_id': self.object.analysis.id})

    def get_queryset(self):
        """Only allow deletion of own visualizations or project owner."""
        return Visualization.objects.filter(
            Q(created_by=self.request.user) |
            Q(analysis__dataset__project__owner=self.request.user)
        )

    def delete(self, request, *args, **kwargs):
        """Delete with message."""
        self.object = self.get_object()
        success_url = self.get_success_url()

        try:
            self.object.delete()
            messages.success(request, f"Visualization '{self.object.title}' deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting visualization {self.object.id}: {e}", exc_info=True)
            messages.error(request, f"Error deleting visualization: {str(e)}")

        return redirect(success_url)


class RegenerateVisualizationView(LoginRequiredMixin, View):
    """
    Regenerate a visualization with updated data.
    """

    def post(self, request, viz_id):
        """Regenerate the visualization."""
        visualization = get_object_or_404(Visualization, id=viz_id)

        # Check permissions
        project = visualization.analysis.dataset.project
        if not (project.owner == request.user or
                request.user in project.collaborators.all()):
            return HttpResponseForbidden("You don't have permission to regenerate this visualization")

        try:
            # Use the existing config
            config = visualization.config or {}

            # Trigger async regeneration
            task = generate_custom_visualization.delay(
                analysis_id=visualization.analysis.id,
                viz_type=visualization.viz_type,
                config=config,
                user_id=request.user.id
            )

            messages.success(
                request,
                f"Regenerating {visualization.get_viz_type_display()}. "
                f"A new version will appear in the gallery shortly."
            )

        except Exception as e:
            logger.error(f"Error regenerating visualization {viz_id}: {e}", exc_info=True)
            messages.error(request, f"Error regenerating visualization: {str(e)}")

        return redirect('visualizations:detail', viz_id=viz_id)


class VisualizationStatusAPIView(LoginRequiredMixin, View):
    """
    API endpoint to check generation status.
    """

    def get(self, request, task_id):
        """Check Celery task status."""
        from celery.result import AsyncResult

        task = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'status': task.state,
            'ready': task.ready(),
        }

        if task.ready():
            if task.successful():
                response_data['result'] = task.result
            else:
                response_data['error'] = str(task.info)

        return JsonResponse(response_data)
