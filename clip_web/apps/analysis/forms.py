"""
Forms for creating and managing analyses.
"""

from django import forms
from apps.analysis.models import Analysis, TextPrompt


class AnalysisCreateForm(forms.ModelForm):
    """
    Form for creating a new CLIP analysis.
    """
    # Text prompts as a textarea (one per line)
    text_prompts = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 8,
            'placeholder': 'Enter text prompts, one per line...\nExample:\narchitecture\nurban landscape\nnatural scenery\npeople and crowds'
        }),
        help_text='Enter text prompts or keywords to compare with images (one per line)',
        label='Text Prompts'
    )

    class Meta:
        model = Analysis
        fields = ['name', 'description', 'model_name']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'model_name': forms.Select(choices=[
                ('openai/clip-vit-base-patch32', 'CLIP ViT-B/32 (Default, Balanced)'),
                ('openai/clip-vit-base-patch16', 'CLIP ViT-B/16 (Higher Quality)'),
                ('openai/clip-vit-large-patch14', 'CLIP ViT-L/14 (Highest Quality, Slower)'),
            ])
        }
        help_texts = {
            'name': 'A descriptive name for this analysis',
            'description': 'Optional: Describe the purpose and goals of this analysis',
            'model_name': 'Choose the CLIP model to use (larger models are more accurate but slower)'
        }

    def clean_text_prompts(self):
        """Parse and validate text prompts."""
        text_prompts = self.cleaned_data.get('text_prompts', '')

        # Split by newlines and filter empty lines
        prompts = [
            line.strip()
            for line in text_prompts.split('\n')
            if line.strip()
        ]

        if len(prompts) == 0:
            raise forms.ValidationError('Please enter at least one text prompt.')

        if len(prompts) > 50:
            raise forms.ValidationError('Maximum 50 text prompts allowed.')

        # Check for duplicates
        if len(prompts) != len(set(prompts)):
            raise forms.ValidationError('Duplicate prompts found. Each prompt must be unique.')

        # Validate individual prompts
        for prompt in prompts:
            if len(prompt) > 500:
                raise forms.ValidationError(f'Prompt too long: "{prompt[:50]}..." (max 500 characters)')
            if len(prompt) < 2:
                raise forms.ValidationError(f'Prompt too short: "{prompt}" (min 2 characters)')

        return prompts

    def save(self, commit=True):
        """Save analysis and create text prompts."""
        analysis = super().save(commit=False)

        if commit:
            analysis.save()

            # Create text prompts
            prompts = self.cleaned_data['text_prompts']
            text_prompt_objects = [
                TextPrompt(
                    analysis=analysis,
                    text=prompt,
                    order=idx
                )
                for idx, prompt in enumerate(prompts)
            ]
            TextPrompt.objects.bulk_create(text_prompt_objects)

        return analysis


class AnalysisUpdateForm(forms.ModelForm):
    """
    Form for updating analysis metadata (not prompts).
    """
    class Meta:
        model = Analysis
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
