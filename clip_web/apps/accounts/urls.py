"""
URLs for accounts app.
"""

from django.urls import path
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', lambda r: None, name='register'),  # TODO: Implement
    path('profile/', lambda r: None, name='profile'),  # TODO: Implement
]
