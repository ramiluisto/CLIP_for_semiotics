"""
Custom permissions for API access control.
"""

from rest_framework import permissions
from apps.projects.models import Project, ProjectMembership


class IsOwnerOrCollaborator(permissions.BasePermission):
    """
    Permission to check if user is project owner or collaborator.
    """

    def has_object_permission(self, request, view, obj):
        # For Project objects
        if isinstance(obj, Project):
            return (
                obj.owner == request.user or
                obj.collaborators.filter(id=request.user.id).exists()
            )

        # For objects with a project attribute
        if hasattr(obj, 'project'):
            project = obj.project
            return (
                project.owner == request.user or
                project.collaborators.filter(id=request.user.id).exists()
            )

        return False


class IsProjectMember(permissions.BasePermission):
    """
    Permission to check if user has access to a project.
    """

    def has_object_permission(self, request, view, obj):
        # Get the project
        if isinstance(obj, Project):
            project = obj
        elif hasattr(obj, 'project'):
            project = obj.project
        else:
            return False

        # Check ownership or membership
        if project.owner == request.user:
            return True

        # Check if user is a collaborator
        try:
            membership = ProjectMembership.objects.get(
                project=project,
                user=request.user
            )

            # For safe methods, all roles can access
            if request.method in permissions.SAFE_METHODS:
                return True

            # For modification, need editor or owner role
            return membership.role in ['owner', 'editor']

        except ProjectMembership.DoesNotExist:
            return False


class CanEditProject(permissions.BasePermission):
    """
    Permission to check if user can edit a project.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            project = obj
        elif hasattr(obj, 'project'):
            project = obj.project
        else:
            return False

        # Owner can always edit
        if project.owner == request.user:
            return True

        # Check membership role
        try:
            membership = ProjectMembership.objects.get(
                project=project,
                user=request.user
            )
            return membership.role in ['owner', 'editor']
        except ProjectMembership.DoesNotExist:
            return False


class CanDeleteProject(permissions.BasePermission):
    """
    Permission to check if user can delete a project.
    Only project owner can delete.
    """

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Project):
            return obj.owner == request.user
        elif hasattr(obj, 'project'):
            return obj.project.owner == request.user
        return False


class IsOwner(permissions.BasePermission):
    """
    Permission to check if user owns the object.
    """

    def has_object_permission(self, request, view, obj):
        # Check various owner fields
        owner_fields = ['owner', 'created_by', 'uploaded_by', 'user']

        for field in owner_fields:
            if hasattr(obj, field):
                owner = getattr(obj, field)
                if owner == request.user:
                    return True

        return False
