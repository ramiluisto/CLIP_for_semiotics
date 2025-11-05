"""
URLs for visualizations app.
"""

from django.urls import path
from . import views

app_name = 'visualizations'

urlpatterns = [
    # Gallery view for specific analysis
    path(
        'analysis/<int:analysis_id>/',
        views.VisualizationGalleryView.as_view(),
        name='gallery'
    ),

    # Detail view for single visualization
    path(
        '<int:viz_id>/',
        views.VisualizationDetailView.as_view(),
        name='detail'
    ),

    # List all visualizations (across analyses)
    path(
        '',
        views.VisualizationListView.as_view(),
        name='list'
    ),

    # Generate visualizations
    path(
        'generate/<int:analysis_id>/',
        views.GenerateVisualizationView.as_view(),
        name='generate'
    ),

    # Delete visualization
    path(
        '<int:viz_id>/delete/',
        views.DeleteVisualizationView.as_view(),
        name='delete'
    ),

    # Regenerate visualization
    path(
        '<int:viz_id>/regenerate/',
        views.RegenerateVisualizationView.as_view(),
        name='regenerate'
    ),

    # API: Check task status
    path(
        'api/status/<str:task_id>/',
        views.VisualizationStatusAPIView.as_view(),
        name='task_status'
    ),
]
