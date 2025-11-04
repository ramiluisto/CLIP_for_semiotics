"""
URLs for images app.
"""

from django.urls import path
from apps.images import views

app_name = 'images'

urlpatterns = [
    # Dataset CRUD
    path('<slug:project_slug>/datasets/',
         views.DatasetListView.as_view(),
         name='dataset_list'),
    path('<slug:project_slug>/datasets/create/',
         views.DatasetCreateView.as_view(),
         name='dataset_create'),
    path('<slug:project_slug>/datasets/<int:dataset_id>/',
         views.DatasetDetailView.as_view(),
         name='dataset_detail'),
    path('<slug:project_slug>/datasets/<int:dataset_id>/edit/',
         views.DatasetUpdateView.as_view(),
         name='dataset_update'),
    path('<slug:project_slug>/datasets/<int:dataset_id>/delete/',
         views.DatasetDeleteView.as_view(),
         name='dataset_delete'),

    # Image upload and management
    path('<slug:project_slug>/datasets/<int:dataset_id>/upload/',
         views.ImageUploadView.as_view(),
         name='image_upload'),
    path('<slug:project_slug>/datasets/<int:dataset_id>/images/<int:image_id>/delete/',
         views.image_delete,
         name='image_delete'),
]
