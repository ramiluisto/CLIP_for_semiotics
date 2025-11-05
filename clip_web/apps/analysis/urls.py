"""
URLs for analysis app.
"""

from django.urls import path
from apps.analysis import views

app_name = 'analysis'

urlpatterns = [
    # Analysis CRUD
    path('<slug:project_slug>/analyses/',
         views.AnalysisListView.as_view(),
         name='list'),
    path('<slug:project_slug>/analyses/create/',
         views.AnalysisCreateView.as_view(),
         name='create'),
    path('<slug:project_slug>/analyses/create/<int:dataset_id>/',
         views.AnalysisCreateView.as_view(),
         name='create_from_dataset'),
    path('<slug:project_slug>/analyses/<int:analysis_id>/',
         views.AnalysisDetailView.as_view(),
         name='detail'),
    path('<slug:project_slug>/analyses/<int:analysis_id>/edit/',
         views.AnalysisUpdateView.as_view(),
         name='update'),
    path('<slug:project_slug>/analyses/<int:analysis_id>/delete/',
         views.AnalysisDeleteView.as_view(),
         name='delete'),

    # Analysis actions
    path('<slug:project_slug>/analyses/<int:analysis_id>/progress/',
         views.analysis_progress,
         name='progress'),
    path('<slug:project_slug>/analyses/<int:analysis_id>/cancel/',
         views.analysis_cancel,
         name='cancel'),

    # HTMX partials
    path('<slug:project_slug>/analyses/<int:analysis_id>/partials/progress/',
         views.analysis_progress_partial,
         name='progress_partial'),
    path('<slug:project_slug>/analyses/<int:analysis_id>/partials/status/',
         views.analysis_status_partial,
         name='status_partial'),
]
