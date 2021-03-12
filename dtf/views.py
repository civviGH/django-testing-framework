
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse

from rest_framework import status

from dtf.serializers import ProjectSerializer
from dtf.serializers import ProjectSubmissionPropertySerializer
from dtf.serializers import WebhookSerializer

from dtf.models import TestResult, Project, ReferenceSet, TestReference, Submission, ProjectSubmissionProperty, Webhook
from dtf.functions import create_view_data_from_test_references, create_reference_query
from dtf.forms import NewProjectForm, ProjectSettingsForm, ProjectSubmissionPropertyForm, WebhookForm

#
# User views
#

def frontpage(request):
    results = TestResult.objects.order_by('-created')[:5]
    return render(request, 'dtf/index.html', {'data':results})

def view_projects(request):
    projects = Project.objects.order_by('-name')
    return render(request, 'dtf/view_projects.html', {'projects':projects})

def view_new_project(request):
    if request.method == 'POST':
        form = NewProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('projects'))
    else:
        form = NewProjectForm()
    return render(request, 'dtf/new_project.html', {
        'form': form}
    )

def view_project_settings(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    properties = project.properties.all()
    webhooks = project.webhooks.all()

    if request.method == 'POST':
        if request.POST.get('scope') == 'project':
            project_form = ProjectSettingsForm(request.POST, instance=project)

            if project_form.is_valid():
                project_form.save()
                serializer = ProjectSerializer(project_form.instance)
                return JsonResponse({'result' : 'valid', 'property' : serializer.data})
            else:
                data = project_form.errors.get_json_data()
                return JsonResponse({'result' : 'invalid', 'errors' : project_form.errors.get_json_data()})

        if request.POST.get('scope') == 'property':
            if request.POST.get('action') == 'add':
                property_form = ProjectSubmissionPropertyForm(request.POST, initial={'project': project,})
            elif request.POST.get('action') == 'edit':
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
                data = property_form.errors.get_json_data()
                return JsonResponse({'result' : 'invalid', 'errors' : property_form.errors.get_json_data()})

        if request.POST.get('scope') == 'webhook':
            if request.POST.get('action') == 'add':
                webhook_form = WebhookForm(request.POST, initial={'project': project,})
            elif request.POST.get('action') == 'edit':
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
                data = webhook_form.errors.get_json_data()
                return JsonResponse({'result' : 'invalid', 'errors' : webhook_form.errors.get_json_data()})

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
        'webhook_form': webhook_form
    })


def view_webhook_log(request, project_slug, webhook_id):
    project = get_object_or_404(Project, slug=project_slug)
    webhook = project.webhooks.get(id=webhook_id)
    return render(request, 'dtf/webhook_log.html', {
        'webhook': webhook,
    })

def view_project_details(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    properties = ProjectSubmissionProperty.objects.filter(project=project)

    paginator = Paginator(project.submissions.order_by('-pk'), per_page=20)

    page_number = request.GET.get('page')
    submissions = paginator.get_page(page_number)

    return render(request, 'dtf/project_details.html', {
        'project':project,
        'properties':properties,
        'submissions':submissions
    })

def view_test_result_details(request, test_id):
    test_result = get_object_or_404(TestResult, pk=test_id)
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

    if test_reference is not None:
        references = test_reference.references
    else:
        references = {}

    data = create_view_data_from_test_references(test_result.results, references)
    nav_data = project.get_nav_data(test_result.name, test_result.submission.id)
    return render(request, 'dtf/test_result_details.html', {
        'project':project,
        'reference_set':reference_set,
        'test_reference':test_reference,
        'test_result':test_result,
        'property_values':str(property_values),
        'data':data,
        'nav_data':nav_data
    })

def view_submission_details(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    return render(request, 'dtf/submission_details.html', {
        'submission':submission
    })
