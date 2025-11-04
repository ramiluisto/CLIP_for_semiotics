"""
Views for CLIP analysis management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, Prefetch

from apps.analysis.models import Analysis, TextPrompt, SimilarityResult
from apps.analysis.forms import AnalysisCreateForm, AnalysisUpdateForm
from apps.projects.models import Project, ProjectMembership
from apps.images.models import ImageDataset, Image


class AnalysisListView(LoginRequiredMixin, ListView):
    """List analyses for a project."""
    model = Analysis
    template_name = 'analysis/analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 12

    def get_queryset(self):
        """Get analyses for the specified project."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )

        # Check access
        user = self.request.user
        if not (self.project.owner == user or
                ProjectMembership.objects.filter(
                    project=self.project,
                    user=user
                ).exists() or
                self.project.is_public):
            return Analysis.objects.none()

        queryset = self.project.analyses.select_related(
            'dataset',
            'created_by'
        ).annotate(
            result_count=Count('results'),
            prompt_count=Count('text_prompts')
        )

        # Filter by status
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Search
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['search'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')

        # Check permissions
        user = self.request.user
        context['can_edit'] = (
            self.project.owner == user or
            ProjectMembership.objects.filter(
                project=self.project,
                user=user,
                role__in=['owner', 'editor']
            ).exists()
        )

        # Get status counts
        context['status_counts'] = {
            'all': self.project.analyses.count(),
            'pending': self.project.analyses.filter(status='pending').count(),
            'processing': self.project.analyses.filter(status='processing').count(),
            'completed': self.project.analyses.filter(status='completed').count(),
            'failed': self.project.analyses.filter(status='failed').count(),
        }

        return context


class AnalysisDetailView(LoginRequiredMixin, DetailView):
    """Show analysis details and results."""
    model = Analysis
    template_name = 'analysis/analysis_detail.html'
    context_object_name = 'analysis'
    pk_url_kwarg = 'analysis_id'

    def get_queryset(self):
        """Filter by project and permissions."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )
        return Analysis.objects.filter(project=self.project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project

        # Get text prompts
        context['text_prompts'] = self.object.text_prompts.all()

        # Get top results for each prompt
        prompt_results = {}
        for prompt in context['text_prompts']:
            top_results = SimilarityResult.objects.filter(
                analysis=self.object,
                text_prompt=prompt
            ).select_related('image').order_by('-similarity_score')[:10]
            prompt_results[prompt.id] = top_results
        context['prompt_results'] = prompt_results

        # Calculate statistics
        if self.object.status == 'completed':
            context['avg_similarity'] = SimilarityResult.objects.filter(
                analysis=self.object
            ).aggregate(avg=Avg('similarity_score'))['avg']

            context['total_results'] = self.object.results.count()

        # Check permissions
        user = self.request.user
        context['can_edit'] = (
            self.project.owner == user or
            ProjectMembership.objects.filter(
                project=self.project,
                user=user,
                role__in=['owner', 'editor']
            ).exists()
        )

        return context


class AnalysisCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new analysis with wizard-style interface."""
    model = Analysis
    form_class = AnalysisCreateForm
    template_name = 'analysis/analysis_create.html'
    success_message = "Analysis '%(name)s' created and queued for processing!"

    def dispatch(self, request, *args, **kwargs):
        """Check permissions and get project/dataset."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )

        # Get dataset if specified in URL
        dataset_id = self.kwargs.get('dataset_id')
        if dataset_id:
            self.dataset = get_object_or_404(
                ImageDataset,
                id=dataset_id,
                project=self.project
            )
        else:
            self.dataset = None

        # Check permissions
        user = request.user
        if not (self.project.owner == user or
                ProjectMembership.objects.filter(
                    project=self.project,
                    user=user,
                    role__in=['owner', 'editor']
                ).exists()):
            messages.error(request, "You don't have permission to create analyses in this project.")
            return redirect('projects:detail', slug=self.project.slug)

        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        """Initialize form with dataset if provided."""
        form = super().get_form(form_class)

        # If no dataset specified, show dataset selection
        if not self.dataset:
            # Add dataset field to form
            form.fields['dataset'] = forms.ModelChoiceField(
                queryset=self.project.datasets.annotate(
                    image_count=Count('images')
                ).filter(image_count__gt=0),
                empty_label='Select a dataset...',
                help_text='Choose the image dataset to analyze'
            )

        return form

    def form_valid(self, form):
        """Set project, dataset, and user, then queue the analysis."""
        from django import forms

        form.instance.project = self.project

        # Set dataset
        if self.dataset:
            form.instance.dataset = self.dataset
        else:
            form.instance.dataset = form.cleaned_data.get('dataset')

        form.instance.created_by = self.request.user
        form.instance.status = 'pending'

        response = super().form_valid(form)

        # Queue the Celery task
        from apps.analysis.tasks import process_analysis_job
        task = process_analysis_job.delay(self.object.id)

        # Save task ID
        self.object.celery_task_id = task.id
        self.object.save()

        return response

    def get_success_url(self):
        return reverse('analysis:detail',
                      kwargs={
                          'project_slug': self.project.slug,
                          'analysis_id': self.object.id
                      })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['dataset'] = self.dataset

        # Get datasets for selection
        if not self.dataset:
            context['datasets'] = self.project.datasets.annotate(
                image_count=Count('images')
            ).filter(image_count__gt=0)

        return context


class AnalysisUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update analysis metadata."""
    model = Analysis
    form_class = AnalysisUpdateForm
    template_name = 'analysis/analysis_form.html'
    pk_url_kwarg = 'analysis_id'
    success_message = "Analysis '%(name)s' updated successfully!"

    def get_queryset(self):
        """Filter by project."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )
        return Analysis.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse('analysis:detail',
                      kwargs={
                          'project_slug': self.project.slug,
                          'analysis_id': self.object.id
                      })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context


class AnalysisDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete an analysis."""
    model = Analysis
    template_name = 'analysis/analysis_confirm_delete.html'
    pk_url_kwarg = 'analysis_id'
    success_message = "Analysis deleted successfully!"

    def get_queryset(self):
        """Filter by project."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )
        return Analysis.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse('analysis:list',
                      kwargs={'project_slug': self.project.slug})

    def delete(self, request, *args, **kwargs):
        """Add success message on delete."""
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context


def analysis_progress(request, project_slug, analysis_id):
    """AJAX endpoint for checking analysis progress."""
    analysis = get_object_or_404(
        Analysis,
        id=analysis_id,
        project__slug=project_slug
    )

    return JsonResponse({
        'status': analysis.status,
        'progress_percentage': analysis.progress_percentage,
        'images_processed': analysis.images_processed,
        'total_images': analysis.total_images,
        'progress_display': analysis.get_progress_display(),
        'error_message': analysis.error_message if analysis.status == 'failed' else None
    })


def analysis_cancel(request, project_slug, analysis_id):
    """Cancel a running analysis."""
    if request.method != 'POST':
        return redirect('analysis:detail',
                       project_slug=project_slug,
                       analysis_id=analysis_id)

    analysis = get_object_or_404(
        Analysis,
        id=analysis_id,
        project__slug=project_slug
    )

    # Check permissions
    project = analysis.project
    user = request.user
    if not (project.owner == user or
            ProjectMembership.objects.filter(
                project=project,
                user=user,
                role__in=['owner', 'editor']
            ).exists()):
        messages.error(request, "You don't have permission to cancel this analysis.")
        return redirect('analysis:detail',
                       project_slug=project_slug,
                       analysis_id=analysis_id)

    # Cancel if pending or processing
    if analysis.status in ['pending', 'processing']:
        # Revoke Celery task
        if analysis.celery_task_id:
            from celery import current_app
            current_app.control.revoke(analysis.celery_task_id, terminate=True)

        analysis.status = 'cancelled'
        analysis.save()
        messages.success(request, f"Analysis '{analysis.name}' cancelled.")
    else:
        messages.warning(request, f"Cannot cancel analysis in '{analysis.status}' status.")

    return redirect('analysis:detail',
                   project_slug=project_slug,
                   analysis_id=analysis_id)
