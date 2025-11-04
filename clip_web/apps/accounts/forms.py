"""
Forms for accounts app.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile


class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    institution = forms.CharField(required=False)
    research_area = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'institution', 'research_area', 'password1', 'password2']


class UserProfileForm(forms.ModelForm):
    """Form for updating user profile."""

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio', 'default_text_prompts', 'notification_preferences']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'default_text_prompts': forms.Textarea(attrs={'rows': 3}),
        }
