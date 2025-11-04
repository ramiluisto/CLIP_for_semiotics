"""
Views for projects app.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.db.models import Q, Count, Prefetch

from apps.projects.models import Project, ProjectMembership
from apps.images.models import ImageDataset
from apps.analysis.models import Analysis


class ProjectAccessMixin(UserPassesTestMixin):
    """Mixin to check if user has access to a project."""

    def test_func(self):
        project = self.get_object()
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


class ProjectEditMixin(UserPassesTestMixin):
    """Mixin to check if user can edit a project."""

    def test_func(self):
        project = self.get_object()
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


class ProjectDeleteMixin(UserPassesTestMixin):
    """Mixin to check if user can delete a project."""

    def test_func(self):
        project = self.get_object()
        return project.owner == self.request.user


class ProjectListView(LoginRequiredMixin, ListView):
    """List all projects for the current user."""
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 12

    def get_queryset(self):
        """Get projects owned by or shared with the current user."""
        user = self.request.user

        # Get search query
        search = self.request.GET.get('search', '')

        # Get filter parameters
        filter_type = self.request.GET.get('filter', 'all')

        # Base queryset with annotations
        queryset = Project.objects.annotate(
            dataset_count=Count('datasets', distinct=True),
            analysis_count=Count('analyses', distinct=True)
        )

        # Filter by user access
        if filter_type == 'owned':
            queryset = queryset.filter(owner=user)
        elif filter_type == 'shared':
            queryset = queryset.filter(
                memberships__user=user
            ).exclude(owner=user)
        else:  # all
            queryset = queryset.filter(
                Q(owner=user) | Q(memberships__user=user)
            ).distinct()

        # Search filter
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )

        return queryset.order_by('-updated_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['filter'] = self.request.GET.get('filter', 'all')

        # Get counts for filter badges
        user = self.request.user
        context['owned_count'] = Project.objects.filter(owner=user).count()
        context['shared_count'] = Project.objects.filter(
            memberships__user=user
        ).exclude(owner=user).distinct().count()
        context['total_count'] = context['owned_count'] + context['shared_count']

        return context


class ProjectDetailView(LoginRequiredMixin, ProjectAccessMixin, DetailView):
    """Show project details with datasets and analyses."""
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        """Optimize queries with prefetch."""
        return Project.objects.prefetch_related(
            Prefetch(
                'datasets',
                queryset=ImageDataset.objects.annotate(
                    image_count=Count('images')
                )
            ),
            Prefetch(
                'analyses',
                queryset=Analysis.objects.select_related('dataset').annotate(
                    result_count=Count('results')
                )
            ),
            'memberships__user'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        project = self.object

        # Check user's role
        context['is_owner'] = project.owner == user

        membership = ProjectMembership.objects.filter(
            project=project,
            user=user
        ).first()

        if membership:
            context['user_role'] = membership.role
            context['can_edit'] = membership.can_edit()
            context['can_delete'] = membership.can_delete()
        else:
            context['user_role'] = 'owner' if context['is_owner'] else 'viewer'
            context['can_edit'] = context['is_owner']
            context['can_delete'] = context['is_owner']

        # Get recent activity
        context['recent_analyses'] = project.analyses.order_by('-created_at')[:5]

        # Get statistics
        context['total_images'] = project.get_image_count()

        return context


class ProjectCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new project."""
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'description', 'is_public', 'tags']
    success_message = "Project '%(name)s' created successfully!"

    def form_valid(self, form):
        """Set the owner to the current user."""
        form.instance.owner = self.request.user
        response = super().form_valid(form)

        # Create owner membership
        ProjectMembership.objects.create(
            project=self.object,
            user=self.request.user,
            role='owner'
        )

        return response

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'slug': self.object.slug})


class ProjectUpdateView(
    LoginRequiredMixin,
    ProjectEditMixin,
    SuccessMessageMixin,
    UpdateView
):
    """Update an existing project."""
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'description', 'is_public', 'tags']
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_message = "Project '%(name)s' updated successfully!"

    def get_success_url(self):
        return reverse_lazy('projects:detail', kwargs={'slug': self.object.slug})


class ProjectDeleteView(
    LoginRequiredMixin,
    ProjectDeleteMixin,
    SuccessMessageMixin,
    DeleteView
):
    """Delete a project."""
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('projects:list')
    success_message = "Project deleted successfully!"

    def delete(self, request, *args, **kwargs):
        """Add success message on delete."""
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class ProjectCollaboratorsView(
    LoginRequiredMixin,
    ProjectEditMixin,
    DetailView
):
    """Manage project collaborators."""
    model = Project
    template_name = 'projects/project_collaborators.html'
    context_object_name = 'project'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object

        # Get all memberships
        context['memberships'] = project.memberships.select_related(
            'user', 'invited_by'
        ).order_by('-joined_at')

        return context


def add_collaborator(request, slug):
    """Add a collaborator to a project."""
    if request.method != 'POST':
        return redirect('projects:detail', slug=slug)

    project = get_object_or_404(Project, slug=slug)

    # Check permissions
    if not (project.owner == request.user or
            ProjectMembership.objects.filter(
                project=project,
                user=request.user,
                role__in=['owner', 'editor']
            ).exists()):
        messages.error(request, "You don't have permission to add collaborators.")
        return redirect('projects:detail', slug=slug)

    # Get user email and role
    email = request.POST.get('email', '').strip()
    role = request.POST.get('role', 'viewer')

    if not email:
        messages.error(request, "Email is required.")
        return redirect('projects:collaborators', slug=slug)

    # Find user by email
    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        messages.error(request, f"No user found with email: {email}")
        return redirect('projects:collaborators', slug=slug)

    # Check if already a member
    if ProjectMembership.objects.filter(project=project, user=user).exists():
        messages.warning(request, f"{user.get_full_name() or user.email} is already a collaborator.")
        return redirect('projects:collaborators', slug=slug)

    # Add collaborator
    ProjectMembership.objects.create(
        project=project,
        user=user,
        role=role,
        invited_by=request.user
    )

    messages.success(
        request,
        f"Added {user.get_full_name() or user.email} as {role}."
    )
    return redirect('projects:collaborators', slug=slug)


def remove_collaborator(request, slug, user_id):
    """Remove a collaborator from a project."""
    if request.method != 'POST':
        return redirect('projects:detail', slug=slug)

    project = get_object_or_404(Project, slug=slug)

    # Check permissions (must be owner)
    if project.owner != request.user:
        messages.error(request, "Only the project owner can remove collaborators.")
        return redirect('projects:detail', slug=slug)

    # Get membership
    membership = get_object_or_404(
        ProjectMembership,
        project=project,
        user_id=user_id
    )

    # Don't allow removing owner
    if membership.role == 'owner':
        messages.error(request, "Cannot remove the project owner.")
        return redirect('projects:collaborators', slug=slug)

    user_name = membership.user.get_full_name() or membership.user.email
    membership.delete()

    messages.success(request, f"Removed {user_name} from the project.")
    return redirect('projects:collaborators', slug=slug)


def update_collaborator_role(request, slug, user_id):
    """Update a collaborator's role."""
    if request.method != 'POST':
        return redirect('projects:detail', slug=slug)

    project = get_object_or_404(Project, slug=slug)

    # Check permissions (must be owner)
    if project.owner != request.user:
        messages.error(request, "Only the project owner can change roles.")
        return redirect('projects:detail', slug=slug)

    # Get membership
    membership = get_object_or_404(
        ProjectMembership,
        project=project,
        user_id=user_id
    )

    # Don't allow changing owner role
    if membership.role == 'owner':
        messages.error(request, "Cannot change the owner's role.")
        return redirect('projects:collaborators', slug=slug)

    # Update role
    new_role = request.POST.get('role', 'viewer')
    if new_role in ['editor', 'viewer']:
        membership.role = new_role
        membership.save()

        user_name = membership.user.get_full_name() or membership.user.email
        messages.success(request, f"Updated {user_name}'s role to {new_role}.")
    else:
        messages.error(request, "Invalid role.")

    return redirect('projects:collaborators', slug=slug)
