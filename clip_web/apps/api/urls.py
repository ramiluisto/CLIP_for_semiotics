"""
URLs for API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from .views import (
    ProjectViewSet,
    ImageDatasetViewSet,
    ImageViewSet,
    AnalysisViewSet,
    VisualizationViewSet,
    ExportJobViewSet
)

app_name = 'api'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'datasets', ImageDatasetViewSet, basename='dataset')
router.register(r'images', ImageViewSet, basename='image')
router.register(r'analyses', AnalysisViewSet, basename='analysis')
router.register(r'visualizations', VisualizationViewSet, basename='visualization')
router.register(r'exports', ExportJobViewSet, basename='export')

urlpatterns = [
    # API versioning
    path('v1/', include(router.urls)),

    # Token authentication
    path('v1/auth/token/', obtain_auth_token, name='api-token'),

    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
]
