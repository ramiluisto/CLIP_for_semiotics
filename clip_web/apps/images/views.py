"""
Views for image dataset and image management.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.views.generic.edit import FormView
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.core.files.storage import default_storage
from django import forms

from apps.images.models import ImageDataset, Image, ImageMetadata, GPSData
from apps.projects.models import Project, ProjectMembership
from apps.projects.views import ProjectAccessMixin, ProjectEditMixin


class DatasetAccessMixin(LoginRequiredMixin):
    """Mixin to check if user has access to a dataset."""

    def test_func(self):
        dataset = self.get_object()
        project = dataset.project
        user = self.request.user

        # Check if user is owner
        if project.owner == user:
            return True

        # Check if user is collaborator
        if ProjectMembership.objects.filter(
            project=project,
            user=user
        ).exists():
            return True

        # Check if project is public
        if project.is_public:
            return True

        return False


class DatasetEditMixin(LoginRequiredMixin):
    """Mixin to check if user can edit a dataset."""

    def test_func(self):
        dataset = self.get_object()
        project = dataset.project
        user = self.request.user

        # Check if user is owner
        if project.owner == user:
            return True

        # Check if user is editor
        membership = ProjectMembership.objects.filter(
            project=project,
            user=user
        ).first()

        return membership and membership.can_edit()


class DatasetForm(forms.ModelForm):
    """Form for creating/editing datasets."""

    class Meta:
        model = ImageDataset
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class DatasetListView(LoginRequiredMixin, ListView):
    """List datasets for a project."""
    model = ImageDataset
    template_name = 'images/dataset_list.html'
    context_object_name = 'datasets'
    paginate_by = 12

    def get_queryset(self):
        """Get datasets for the specified project."""
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
            return ImageDataset.objects.none()

        queryset = self.project.datasets.annotate(
            image_count=Count('images')
        )

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


class DatasetDetailView(LoginRequiredMixin, DetailView):
    """Show dataset details with images."""
    model = ImageDataset
    template_name = 'images/dataset_detail.html'
    context_object_name = 'dataset'
    pk_url_kwarg = 'dataset_id'

    def get_queryset(self):
        """Filter by project and permissions."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )
        return ImageDataset.objects.filter(project=self.project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project

        # Get images with metadata
        images = self.object.images.select_related(
            'metadata',
            'gps_data'
        ).order_by('-uploaded_at')

        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(images, 24)  # 24 images per page
        page = self.request.GET.get('page', 1)
        context['images'] = paginator.get_page(page)

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

        # Statistics
        context['total_images'] = self.object.images.count()
        context['images_with_gps'] = self.object.images.filter(
            metadata__has_gps=True
        ).count()
        context['total_size'] = self.object.get_total_size()

        return context


class DatasetCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new dataset."""
    model = ImageDataset
    form_class = DatasetForm
    template_name = 'images/dataset_form.html'
    success_message = "Dataset '%(name)s' created successfully!"

    def dispatch(self, request, *args, **kwargs):
        """Check permissions before proceeding."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )

        # Check if user can edit project
        user = request.user
        if not (self.project.owner == user or
                ProjectMembership.objects.filter(
                    project=self.project,
                    user=user,
                    role__in=['owner', 'editor']
                ).exists()):
            messages.error(request, "You don't have permission to create datasets in this project.")
            return redirect('projects:detail', slug=self.project.slug)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Set the project and created_by."""
        form.instance.project = self.project
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('images:dataset_detail',
                      kwargs={
                          'project_slug': self.project.slug,
                          'dataset_id': self.object.id
                      })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context


class DatasetUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Update a dataset."""
    model = ImageDataset
    form_class = DatasetForm
    template_name = 'images/dataset_form.html'
    pk_url_kwarg = 'dataset_id'
    success_message = "Dataset '%(name)s' updated successfully!"

    def get_queryset(self):
        """Filter by project."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )
        return ImageDataset.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse('images:dataset_detail',
                      kwargs={
                          'project_slug': self.project.slug,
                          'dataset_id': self.object.id
                      })

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context


class DatasetDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    """Delete a dataset."""
    model = ImageDataset
    template_name = 'images/dataset_confirm_delete.html'
    pk_url_kwarg = 'dataset_id'
    success_message = "Dataset deleted successfully!"

    def get_queryset(self):
        """Filter by project."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )
        return ImageDataset.objects.filter(project=self.project)

    def get_success_url(self):
        return reverse('images:dataset_list',
                      kwargs={'project_slug': self.project.slug})

    def delete(self, request, *args, **kwargs):
        """Add success message on delete."""
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context


class ImageUploadView(LoginRequiredMixin, FormView):
    """Handle multiple image uploads."""
    template_name = 'images/image_upload.html'

    def dispatch(self, request, *args, **kwargs):
        """Get dataset and check permissions."""
        self.project = get_object_or_404(
            Project,
            slug=self.kwargs['project_slug']
        )
        self.dataset = get_object_or_404(
            ImageDataset,
            id=self.kwargs['dataset_id'],
            project=self.project
        )

        # Check permissions
        user = request.user
        if not (self.project.owner == user or
                ProjectMembership.objects.filter(
                    project=self.project,
                    user=user,
                    role__in=['owner', 'editor']
                ).exists()):
            messages.error(request, "You don't have permission to upload images.")
            return redirect('images:dataset_detail',
                          project_slug=self.project.slug,
                          dataset_id=self.dataset.id)

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Handle file uploads via AJAX."""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            files = request.FILES.getlist('files')
            uploaded = []

            for file in files:
                try:
                    # Create image instance
                    image = Image(
                        dataset=self.dataset,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        uploaded_by=request.user
                    )

                    # Save will extract metadata via model's save method
                    image.save()

                    # Extract EXIF data and GPS
                    from apps.images.utils import extract_metadata, extract_gps_data

                    metadata = extract_metadata(image.file.path)
                    if metadata:
                        ImageMetadata.objects.create(
                            image=image,
                            exif_data=metadata.get('exif', {}),
                            has_gps=metadata.get('has_gps', False),
                            camera_make=metadata.get('camera_make', ''),
                            camera_model=metadata.get('camera_model', ''),
                            date_taken=metadata.get('date_taken')
                        )

                    gps = extract_gps_data(image.file.path)
                    if gps:
                        GPSData.objects.create(
                            image=image,
                            latitude=gps['latitude'],
                            longitude=gps['longitude'],
                            altitude=gps.get('altitude')
                        )

                    uploaded.append({
                        'id': image.id,
                        'filename': image.original_filename,
                        'size': image.file_size,
                        'url': image.file.url
                    })

                except Exception as e:
                    return JsonResponse({
                        'error': str(e),
                        'filename': file.name
                    }, status=400)

            return JsonResponse({
                'success': True,
                'uploaded': uploaded,
                'count': len(uploaded)
            })

        # Regular form submission redirect
        return redirect('images:dataset_detail',
                       project_slug=self.project.slug,
                       dataset_id=self.dataset.id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        context['dataset'] = self.dataset
        return context


def image_delete(request, project_slug, dataset_id, image_id):
    """Delete an image."""
    if request.method != 'POST':
        return redirect('images:dataset_detail',
                       project_slug=project_slug,
                       dataset_id=dataset_id)

    project = get_object_or_404(Project, slug=project_slug)
    dataset = get_object_or_404(ImageDataset, id=dataset_id, project=project)
    image = get_object_or_404(Image, id=image_id, dataset=dataset)

    # Check permissions
    user = request.user
    if not (project.owner == user or
            ProjectMembership.objects.filter(
                project=project,
                user=user,
                role__in=['owner', 'editor']
            ).exists()):
        messages.error(request, "You don't have permission to delete images.")
        return redirect('images:dataset_detail',
                       project_slug=project_slug,
                       dataset_id=dataset_id)

    # Delete file from storage
    if image.file:
        default_storage.delete(image.file.name)
    if image.thumbnail:
        default_storage.delete(image.thumbnail.name)

    filename = image.original_filename
    image.delete()

    messages.success(request, f"Image '{filename}' deleted successfully!")
    return redirect('images:dataset_detail',
                   project_slug=project_slug,
                   dataset_id=dataset_id)
