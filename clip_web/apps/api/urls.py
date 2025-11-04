"""
URLs for API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'api'

router = DefaultRouter()
# TODO: Register viewsets
# router.register(r'projects', ProjectViewSet)
# router.register(r'analyses', AnalysisViewSet)

urlpatterns = [
    path('v1/', include(router.urls)),
]
