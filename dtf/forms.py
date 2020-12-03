from django import forms
from django.forms import TextInput
from django.utils.safestring import mark_safe

from dtf.models import Project, ProjectSubmissionProperty

class NewProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ['name', 'slug']
        widgets = {
            'name': TextInput(attrs={'placeholder': 'My new project'}),
            'slug': TextInput(attrs={'placeholder': 'my-new-project'}),
        }

class ProjectSettingsForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ['name', 'slug']

class ProjectSubmissionPropertyForm(forms.ModelForm):

    class Meta:
        model = ProjectSubmissionProperty

        fields = ['name', 'required', 'display', 'display_replace', 'display_as_link', 'influence_reference']
        widgets = {
            'name': TextInput(attrs={'placeholder': 'Enter new property...'}),
        }
        help_texts = {
            'display_replace': mark_safe('Use <b>{VALUE}</b> as a placeholder'),
        }
