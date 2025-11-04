"""
URLs for projects app.
"""

from django.urls import path

app_name = 'projects'

urlpatterns = [
    # TODO: Implement views
    path('', lambda r: None, name='list'),
    path('<slug:slug>/', lambda r: None, name='detail'),
    path('create/', lambda r: None, name='create'),
]
