"""
Views for accounts app.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .models import User, UserProfile
from .forms import UserRegistrationForm, UserProfileForm


class RegisterView(CreateView):
    """User registration view."""
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            'Account created successfully! Please log in.'
        )
        return response


@login_required
def profile_view(request):
    """User profile view."""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)

    context = {
        'form': form,
        'storage_used': user.get_storage_used(),
        'storage_percentage': profile.storage_usage_percentage(),
    }
    return render(request, 'accounts/profile.html', context)


# Error handlers
def handler404(request, exception=None):
    """404 error handler."""
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """500 error handler."""
    return render(request, 'errors/500.html', status=500)
