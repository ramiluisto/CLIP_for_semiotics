"""
URLs for analysis app.
"""

from django.urls import path

app_name = 'analysis'

urlpatterns = [
    # TODO: Implement views
    path('<int:pk>/', lambda r: None, name='detail'),
    path('create/', lambda r: None, name='create'),
]
