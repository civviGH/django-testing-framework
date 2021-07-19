from django import forms
from django.forms import TextInput, PasswordInput
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from dtf.models import Project, ProjectSubmissionProperty, Webhook

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
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = ProjectSubmissionProperty

        fields = [
            'project',
            'name',
            'required',
            'influence_reference',
            'display',
            'display_as_link',
            'display_replace',
        ]
        widgets = {
            'name': TextInput(attrs={'placeholder': 'My property'}),
            'display_replace': TextInput(attrs={'placeholder': 'http://example.com/some/path/{VALUE}'}),
            'project': forms.HiddenInput()
        }
        help_texts = {
            'required': "Decline new submission that do not provide a value for this property.",
            'influence_reference': "Include values for this property to find the references of a submission.",
            'display': "Show the values for this property in a separate column in the submission table.",
            'display_as_link': "Show this value as a link in the submission table.",
            'display_replace': mark_safe('Instead of the value of this property, this text will be displayed. Use <b>{VALUE}</b> as a placeholder for the original value.'),
        }

class WebhookForm(forms.ModelForm):
    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Webhook

        fields = [
            'project',
            'name',
            'url',
            'secret_token',
            'on_submission',
            'on_test_result',
            'on_reference_set',
            'on_test_reference'
        ]
        widgets = {
            'name': TextInput(attrs={'placeholder': 'My webhook'}),
            'url': TextInput(attrs={'placeholder': 'http://example.com/my/hook/path'}),
            'project': forms.HiddenInput()
        }
        help_texts = {
            'secret_token': mark_safe('This is send in the reqest header as <b>X-DTF-Token</b> and should be used by the client to authenticate the payload.'),
            'on_submission': 'Trigger when a submission is created, modified or deleted.',
            'on_test_result': 'Trigger when test results for a submission are created, modified or deleted.',
            'on_reference_set': 'Trigger when a reference set is created, modified or deleted.',
            'on_test_reference': 'Trigger when test references are created, modified or deleted.',
        }

class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['placeholder'] = "Username"
        self.fields['password'].widget.attrs['placeholder'] = "Password"

class NewUserForm(forms.ModelForm):

    password = forms.CharField(
        strip=False,
        widget=PasswordInput(attrs={'placeholder': 'Password', 'autocomplete': 'new-password'}),
        # help_text=password_validation.password_validators_help_text_html()
    )

    class Meta:
        model = User
        fields = ("first_name","last_name","username","email")
        widgets = {
            'first_name': TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': TextInput(attrs={'placeholder': 'Last Name'}),
            'username': TextInput(attrs={'placeholder': 'Username'}),
            'email': TextInput(attrs={'placeholder': 'Email address', 'autocomplete': 'email'}),
        }
        help_texts = {
            'username': None
        }

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get('password')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error('password', error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class ResetPasswordForm(PasswordResetForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].widget.attrs['placeholder'] = "Email address"

class PasswordSetForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['new_password1'].widget.attrs['placeholder'] = "New password"
        self.fields['new_password2'].widget.attrs['placeholder'] = "Confirm password"
        self.fields['new_password1'].help_text = None
        self.fields['new_password2'].help_text = None
