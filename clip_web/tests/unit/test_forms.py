"""
Unit tests for Django forms.
"""

import pytest
from apps.analysis.forms import AnalysisCreateForm
from apps.accounts.forms import UserRegistrationForm

pytestmark = [pytest.mark.forms, pytest.mark.django_db]


class TestAnalysisCreateForm:
    """Tests for AnalysisCreateForm."""

    def test_valid_form(self):
        """Test form with valid data."""
        data = {
            'name': 'Test Analysis',
            'description': 'Test description',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': 'architecture\nnature\npeople'
        }
        form = AnalysisCreateForm(data=data)
        assert form.is_valid()

    def test_text_prompts_parsing(self):
        """Test that text prompts are correctly parsed."""
        data = {
            'name': 'Test',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': 'prompt1\nprompt2\nprompt3'
        }
        form = AnalysisCreateForm(data=data)
        assert form.is_valid()
        prompts = form.cleaned_data['text_prompts']
        assert len(prompts) == 3
        assert 'prompt1' in prompts

    def test_empty_prompts_invalid(self):
        """Test that empty prompts are invalid."""
        data = {
            'name': 'Test',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': ''
        }
        form = AnalysisCreateForm(data=data)
        assert not form.is_valid()
        assert 'text_prompts' in form.errors

    def test_too_many_prompts(self):
        """Test validation for too many prompts."""
        prompts = '\n'.join([f'prompt{i}' for i in range(51)])  # 51 prompts
        data = {
            'name': 'Test',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': prompts
        }
        form = AnalysisCreateForm(data=data)
        assert not form.is_valid()
        assert 'text_prompts' in form.errors

    def test_duplicate_prompts_invalid(self):
        """Test that duplicate prompts are invalid."""
        data = {
            'name': 'Test',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': 'duplicate\nduplicate\nother'
        }
        form = AnalysisCreateForm(data=data)
        assert not form.is_valid()
        assert 'text_prompts' in form.errors

    def test_prompt_too_long(self):
        """Test validation for prompt length."""
        long_prompt = 'a' * 501  # Over 500 character limit
        data = {
            'name': 'Test',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': long_prompt
        }
        form = AnalysisCreateForm(data=data)
        assert not form.is_valid()

    def test_whitespace_trimming(self):
        """Test that whitespace is properly trimmed."""
        data = {
            'name': 'Test',
            'model_name': 'openai/clip-vit-base-patch32',
            'text_prompts': '  prompt1  \n\n  prompt2  \n\n'
        }
        form = AnalysisCreateForm(data=data)
        assert form.is_valid()
        prompts = form.cleaned_data['text_prompts']
        assert len(prompts) == 2
        assert 'prompt1' in prompts
        assert 'prompt2' in prompts


class TestUserRegistrationForm:
    """Tests for UserRegistrationForm."""

    def test_valid_registration(self):
        """Test form with valid registration data."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'institution': 'Test University',
            'research_area': 'Visual Studies'
        }
        form = UserRegistrationForm(data=data)
        assert form.is_valid()

    def test_password_mismatch(self):
        """Test validation for password mismatch."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!',
            'institution': 'Test University',
            'research_area': 'Visual Studies'
        }
        form = UserRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'password2' in form.errors

    def test_duplicate_username(self, user):
        """Test validation for duplicate username."""
        data = {
            'username': 'testuser',  # Already exists
            'email': 'different@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'institution': 'Test University',
            'research_area': 'Visual Studies'
        }
        form = UserRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'username' in form.errors

    def test_duplicate_email(self, user):
        """Test validation for duplicate email."""
        data = {
            'username': 'differentuser',
            'email': 'test@example.com',  # Already exists
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'institution': 'Test University',
            'research_area': 'Visual Studies'
        }
        form = UserRegistrationForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors
