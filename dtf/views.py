
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, Http404
from django.urls import reverse, reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.views import generic

from rest_framework import status

from dtf.serializers import ProjectSerializer
from dtf.serializers import MembershipSerializer
from dtf.serializers import ProjectSubmissionPropertySerializer
from dtf.serializers import WebhookSerializer

from dtf.models import TestResult, Membership, Project, ReferenceSet, TestReference, Submission, ProjectSubmissionProperty, Webhook, WebhookLogEntry
from dtf.functions import create_reference_query
from dtf.forms import NewProjectForm, ProjectSettingsForm, ProjectSubmissionPropertyForm, MembershipForm, WebhookForm, NewUserForm, LoginForm, ResetPasswordForm, PasswordSetForm
from dtf.permissions import ProjectPermissionRequiredMixin, has_required_model_role, get_model_permissions, check_required_model_role

def _get_project_sidebar_items(user, project):
    result = []
    if has_required_model_role(user, project, Submission, 'view'):
        result.append('submissions')
    if has_required_model_role(user, project, ReferenceSet, 'view'):
        result.append('references')
    if has_required_model_role(user, project, Membership, 'view'):
        result.append('members')
    if has_required_model_role(user, project, Project, 'view') and \
       has_required_model_role(user, project, ProjectSubmissionProperty, 'view') and \
       has_required_model_role(user, project, Webhook, 'view'):
        result.append('settings')
    return result

#
# User views
#

class SignUpView(generic.FormView):
    template_name = 'dtf/users/sign_up.html'
    form_class = NewUserForm
    success_url = reverse_lazy('projects')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class SignInView(LoginView):
    form_class = LoginForm
    template_name = 'dtf/users/sign_in.html'

    def form_valid(self, form):
        remember_me = form.cleaned_data['remember_me']
        if not remember_me:
             self.request.session.set_expiry(0)
             self.request.session.modified = True
        return super().form_valid(form)

class SignOutView(LogoutView):
    template_name = 'dtf/users/sign_out.html'

class ResetPasswordView(PasswordResetView):
    form_class = ResetPasswordForm
    template_name = 'dtf/users/reset_password.html'
    email_template_name = 'dtf/users/reset_password_email.html'
    success_url = reverse_lazy('reset_password_done')

class ResetPasswordDoneView(PasswordResetDoneView):
    template_name = 'dtf/users/reset_password_done.html'

class ResetPasswordConfirmView(PasswordResetConfirmView):
    form_class = PasswordSetForm
    template_name = 'dtf/users/reset_password_confirm.html'
    success_url = reverse_lazy('reset_password_complete')

class ResetPasswordCompleteView(PasswordResetCompleteView):
    template_name = 'dtf/users/reset_password_complete.html'

#
# Project views
#

class ProjectViewMixin():
    project_slug_url_kwarg = 'project_slug'

    def get_project(self):
        return get_object_or_404(Project, slug=self.kwargs[self.project_slug_url_kwarg])

    def get_context_data(self, **kwargs):
        project = self.get_project()
        return super().get_context_data(**kwargs,
                                        project_sidebar_items=_get_project_sidebar_items(self.request.user, project))

class ProjectListView(generic.ListView):
    template_name = 'dtf/view_projects.html'
    model = Project
    ordering = '-name'
    context_object_name = 'projects'

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                return Project.objects.order_by(self.ordering)
            else:
                return self.request.user.projects.order_by(self.ordering)
        return []

class NewProjectView(LoginRequiredMixin, generic.FormView):
    template_name = 'dtf/new_project.html'
    form_class = NewProjectForm
    success_url = reverse_lazy('projects')

    def form_valid(self, form):
        form.save()
        form.instance.memberships.create(user=self.request.user, role='owner')
        return super().form_valid(form)

class ProjectMembersView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.UpdateView):
    template_name = 'dtf/project_members.html'
    model = Membership
    form_class = MembershipForm

    def get_requested_operations(self, request, model, **kwargs):
        requested_operations = ['view']
        if request.method == 'POST':
            if self.request.POST.get('action') == 'add':
                requested_operations.append('add')
            elif self.request.POST.get('action') == 'edit':
                requested_operations.append('change')
            else:
                requested_operations.append(None)
        return requested_operations

    def get_queryset(self):
        return self.get_project().memberships.all()

    def get_initial(self):
        return {'project': self.get_project()}

    def get_object(self):
        if self.request.method == 'POST' and self.request.POST.get('action') == 'edit':
            queryset = self.get_queryset()
            try:
                return queryset.get(pk=self.request.POST.get('id', None))
            except queryset.model.DoesNotExist:
                raise Http404(_("No %(verbose_name)s found matching the query") %
                               {'verbose_name': queryset.model._meta.verbose_name})
        return None

    def form_valid(self, form):
        form.save()
        serializer = MembershipSerializer(form.instance)
        return JsonResponse({'result' : 'valid', 'member' : serializer.data})

    def form_invalid(self, form):
        errors = form.errors.get_json_data()
        return JsonResponse({'result' : 'invalid', 'errors' : errors})

    def get_context_data(self, **kwargs):
        project = self.get_project()
        return super().get_context_data(**kwargs,
                                        project=project,
                                        member_permissions=get_model_permissions(self.request.user, project, Membership))

@login_required
def view_project_settings(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)

    check_required_model_role(request.user, project, Project, 'view')
    check_required_model_role(request.user, project, ProjectSubmissionProperty, 'view')
    check_required_model_role(request.user, project, Webhook, 'view')

    properties = project.properties.all()
    webhooks = project.webhooks.all()

    if request.method == 'POST':
        if request.POST.get('scope') == 'project':
            check_required_model_role(request.user, project, Project, 'change')

            project_form = ProjectSettingsForm(request.POST, instance=project)

            if project_form.is_valid():
                project_form.save()
                serializer = ProjectSerializer(project_form.instance, context={"request": request})
                return JsonResponse({'result' : 'valid', 'property' : serializer.data})
            else:
                errors = project_form.errors.get_json_data()
                return JsonResponse({'result' : 'invalid', 'errors' : errors})

        if request.POST.get('scope') == 'property':
            if request.POST.get('action') == 'add':
                check_required_model_role(request.user, project, ProjectSubmissionProperty, 'add')
                property_form = ProjectSubmissionPropertyForm(request.POST, initial={'project': project,})
            elif request.POST.get('action') == 'edit':
                check_required_model_role(request.user, project, ProjectSubmissionProperty, 'change')
                try:
                    prop = ProjectSubmissionProperty.objects.get(pk=request.POST.get('id', None))
                except ProjectSubmissionProperty.DoesNotExist:
                    return HttpResponse(status=status.HTTP_404_NOT_FOUND)
                property_form = ProjectSubmissionPropertyForm(request.POST, initial={'project': project,}, instance=prop)
            else:
                return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

            if property_form.is_valid():
                property_form.save()
                serializer = ProjectSubmissionPropertySerializer(property_form.instance)
                return JsonResponse({'result' : 'valid', 'property' : serializer.data})
            else:
                errors = property_form.errors.get_json_data()
                return JsonResponse({'result' : 'invalid', 'errors' : errors})

        if request.POST.get('scope') == 'webhook':
            if request.POST.get('action') == 'add':
                check_required_model_role(request.user, project, Webhook, 'add')
                webhook_form = WebhookForm(request.POST, initial={'project': project,})
            elif request.POST.get('action') == 'edit':
                check_required_model_role(request.user, project, Webhook, 'change')
                try:
                    webhook = Webhook.objects.get(pk=request.POST.get('id', None))
                except Webhook.DoesNotExist:
                    return HttpResponse(status=status.HTTP_404_NOT_FOUND)
                webhook_form = WebhookForm(request.POST, initial={'project': project,}, instance=webhook)
            else:
                return HttpResponse(status=status.HTTP_400_BAD_REQUEST)

            if webhook_form.is_valid():
                webhook_form.save()
                serializer = WebhookSerializer(webhook_form.instance)
                return JsonResponse({'result' : 'valid', 'webhook' : serializer.data})
            else:
                errors = webhook_form.errors.get_json_data()
                return JsonResponse({'result' : 'invalid', 'errors' : errors})

    # Not any valid POST request: return the site
    project_form = ProjectSettingsForm(instance=project)
    property_form = ProjectSubmissionPropertyForm(initial={'project': project})
    webhook_form = WebhookForm(initial={'project': project,})
    return render(request, 'dtf/project_settings.html', {
        'project': project,
        'project_form': project_form,
        'properties' : properties,
        'property_form': property_form,
        'webhooks' : webhooks,
        'webhook_form': webhook_form,
        'project_sidebar_items': _get_project_sidebar_items(request.user, project),
        'project_permissions': get_model_permissions(request.user, project, Project),
        'property_permissions': get_model_permissions(request.user, project, ProjectSubmissionProperty),
        'webhook_permissions': get_model_permissions(request.user, project, Webhook),
        'webhook_log_permissions': get_model_permissions(request.user, project, WebhookLogEntry, operations=['view'])
    })


class WebhookDetailView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.DetailView):
    template_name = 'dtf/webhook_log.html'
    model = WebhookLogEntry
    context_object_name = 'webhook'
    pk_url_kwarg = 'webhook_id'

    def get_queryset(self):
        return self.get_project().webhooks.all()

class ProjectSubmissionListView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.ListView):
    template_name = 'dtf/project_submissions.html'
    model = Submission
    ordering = '-created'
    paginate_by = 20

    def get_queryset(self):
        return self.get_project().submissions.order_by(self.ordering)

    def get_context_data(self, **kwargs):
        project = self.get_project()
        return super().get_context_data(**kwargs, project=project, properties=project.properties.all())

class TestResultDetailView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.DetailView):
    template_name = 'dtf/test_result_details.html'
    model = TestResult
    permission_models = [TestResult, TestReference]
    context_object_name = 'test_result'
    pk_url_kwarg = 'test_id'

    def get_queryset(self):
        return TestResult.objects.filter(submission__project=self.get_project())

    def get_context_data(self, **kwargs):
        test_result = self.object
        submission = test_result.submission
        project = submission.project

        queries = create_reference_query(project, submission.info)

        reference_set = None
        property_values = None
        test_reference = None
        try:
            reference_set = project.reference_sets.get(**queries)
            if reference_set.test_references.exists():
                try:
                    test_reference = reference_set.test_references.get(test_name=test_result.name)
                except TestReference.DoesNotExist:
                    test_reference = None
        except ReferenceSet.DoesNotExist:
            property_values = {}
            for prop in project.properties.all():
                if prop.influence_reference:
                    prop_value = submission.info.get(prop.name, None)
                    if not prop_value is None:
                        property_values[prop.name] = prop_value

        # nav_data = project.get_nav_data(test_result.name, test_result.submission.id)
        return super().get_context_data(**kwargs,
                                        project=project,
                                        reference_set=reference_set,
                                        test_reference=test_reference,
                                        test_result=test_result,
                                        property_values=property_values,
                                        placeholder_range=range(10),
                                        #nav_data=nav_data,
                                        test_reference_permissions=get_model_permissions(self.request.user, project, TestReference))

class SubmissionDetailView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.DetailView):
    template_name = 'dtf/submission_details.html'
    model = Submission
    context_object_name = 'submission'
    pk_url_kwarg = 'submission_id'

    def get_queryset(self):
        return self.get_project().submissions.all()

class ProjectReferenceSetListView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.ListView):
    template_name = 'dtf/project_reference_sets.html'
    model = ReferenceSet
    ordering = '-created'
    paginate_by = 20

    def get_queryset(self):
        return self.get_project().reference_sets.order_by(self.ordering)

    def get_context_data(self, **kwargs):
        project = self.get_project()
        return super().get_context_data(**kwargs, project=project, properties=project.properties.all())

class ReferenceSetDetailView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.DetailView):
    template_name = 'dtf/reference_set_details.html'
    model = ReferenceSet
    context_object_name = 'reference_set'
    pk_url_kwarg = 'reference_id'

    def get_queryset(self):
        return self.get_project().reference_sets.all()

class TestReferenceDetailView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.DetailView):
    template_name = 'dtf/test_reference_details.html'
    model = TestReference
    context_object_name = 'test_reference'
    pk_url_kwarg = 'test_id'

    def get_queryset(self):
        return TestReference.objects.filter(reference_set__project=self.get_project())

class TestReferenceDetailView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.DetailView):
    template_name = 'dtf/test_reference_details.html'
    model = TestReference
    context_object_name = 'test_reference'
    pk_url_kwarg = 'test_id'

    def get_queryset(self):
        return TestReference.objects.filter(reference_set__project=self.get_project())

class TestMeasurementHistoryView(ProjectViewMixin, ProjectPermissionRequiredMixin, generic.DetailView):
    template_name = 'dtf/test_measurement_history.html'
    model = TestResult
    permission_models = [TestResult, TestReference]
    context_object_name = 'test_result'
    pk_url_kwarg = 'test_id'

    def get_queryset(self):
        return TestResult.objects.filter(submission__project=self.get_project())

    def get_context_data(self, **kwargs):
        test_result = self.object
        submission = test_result.submission
        project = submission.project

        measurement_name = self.request.GET.get('measurement_name')
        limit = self.request.GET.get('limit')

        queries = create_reference_query(project, submission.info)

        test_reference = None
        try:
            reference_set = project.reference_sets.get(**queries)
            if reference_set.test_references.exists():
                try:
                    test_reference = reference_set.test_references.get(test_name=test_result.name)
                except TestReference.DoesNotExist:
                    test_reference = None
        except ReferenceSet.DoesNotExist:
            pass

        measurement_global_reference = None
        if test_reference is not None:
            reference = test_reference.references.get(measurement_name)
            if reference is not None:
                measurement_global_reference = reference['value']

        return super().get_context_data(**kwargs,
                                        display_timezone=settings.DTF_DEFAULT_DISPLAY_TIME_ZONE,
                                        measurement_name=measurement_name,
                                        limit=limit,
                                        measurement_global_reference=measurement_global_reference)

#
# Error views
#

def view_error_403(request, *args, **argv):
    return render(request, 'dtf/errors/403.html')
