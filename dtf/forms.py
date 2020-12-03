from django import forms
from django.forms import TextInput

from dtf.models import Project

class NewProjectForm(forms.ModelForm):

    class Meta:
        model = Project
        fields = ['name', 'slug']
        widgets = {
            'name': TextInput(attrs={'placeholder': 'My new project'}),
            'slug': TextInput(attrs={'placeholder': 'my-new-project'}),
        }
