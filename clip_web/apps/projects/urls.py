"""
URLs for projects app.
"""

from django.urls import path
from apps.projects import views

app_name = 'projects'

urlpatterns = [
    # Project CRUD
    path('', views.ProjectListView.as_view(), name='list'),
    path('create/', views.ProjectCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.ProjectUpdateView.as_view(), name='update'),
    path('<slug:slug>/delete/', views.ProjectDeleteView.as_view(), name='delete'),

    # Collaborator management
    path('<slug:slug>/collaborators/', views.ProjectCollaboratorsView.as_view(), name='collaborators'),
    path('<slug:slug>/collaborators/add/', views.add_collaborator, name='add_collaborator'),
    path('<slug:slug>/collaborators/<int:user_id>/remove/', views.remove_collaborator, name='remove_collaborator'),
    path('<slug:slug>/collaborators/<int:user_id>/update/', views.update_collaborator_role, name='update_collaborator_role'),
]
