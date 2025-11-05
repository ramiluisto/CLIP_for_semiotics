"""
URL configuration for CLIP for Humanists.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Home
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Apps
    path('accounts/', include('apps.accounts.urls')),
    path('projects/', include('apps.projects.urls')),
    path('images/', include('apps.images.urls')),
    path('analysis/', include('apps.analysis.urls')),
    path('visualizations/', include('apps.visualizations.urls')),

    # API (includes schema/docs endpoints)
    path('api/', include('apps.api.urls')),

    # DRF Auth
    path('api-auth/', include('rest_framework.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Custom error handlers
handler404 = 'apps.accounts.views.handler404'
handler500 = 'apps.accounts.views.handler500'
