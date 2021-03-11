
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.forms import inlineformset_factory

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from dtf.serializers import ProjectSerializer
from dtf.serializers import TestResultSerializer
from dtf.serializers import ReferenceSetSerializer
from dtf.serializers import TestReferenceSerializer
from dtf.serializers import SubmissionSerializer
from dtf.serializers import ProjectSubmissionPropertySerializer
from dtf.serializers import WebhookSerializer
from dtf.serializers import WebhookLogEntrySerializer

from dtf.models import TestResult, Project, ReferenceSet, TestReference, Submission, ProjectSubmissionProperty, Webhook
from dtf.functions import create_view_data_from_test_references, get_project_by_id_or_slug, create_reference_query
from dtf.forms import NewProjectForm, ProjectSettingsForm, ProjectSubmissionPropertyForm, WebhookForm

"""
User views
"""

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

"""
Project API endpoints
"""

@api_view(["GET", "POST"])
def projects(request):
    if request.method == 'GET':
        projects = Project.objects.order_by('-pk')
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "DELETE"])
def project(request, id):
    project = get_project_by_id_or_slug(id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProjectSerializer(project)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ProjectSerializer(project, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        project.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

"""
Project Submission Properties API endpoints
"""

@api_view(["GET", "POST"])
def project_submission_properties(request, project_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        properties = ProjectSubmissionProperty.objects.filter(project=project).order_by('-pk')
        serializer = ProjectSubmissionPropertySerializer(properties, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        request.data['project'] = project.id
        serializer = ProjectSubmissionPropertySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "DELETE"])
def project_submission_property(request, project_id, property_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        prop = ProjectSubmissionProperty.objects.get(project=project, pk=property_id)
    except ProjectSubmissionProperty.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ProjectSubmissionPropertySerializer(prop)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ProjectSubmissionPropertySerializer(prop, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        prop.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

"""
Project Webhook API endpoints
"""

@api_view(["GET", "POST"])
def project_webhooks(request, project_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        webhooks = Webhook.objects.filter(project=project).order_by('-pk')
        serializer = WebhookSerializer(webhooks, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        request.data['project'] = project.id
        serializer = WebhookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "DELETE"])
def project_webhook(request, project_id, webhook_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        webhook = Webhook.objects.get(project=project, pk=webhook_id)
    except Webhook.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WebhookSerializer(webhook)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = WebhookSerializer(webhook, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        webhook.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["GET"])
def project_webhook_logs(request, project_id, webhook_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        webhook = Webhook.objects.get(project=project, pk=webhook_id)
    except Webhook.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WebhookLogEntrySerializer(webhook.logs, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

"""
Project Submission API endpoints
"""

@api_view(["GET", "POST"])
def project_submissions(request, project_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        submissions = Submission.objects.filter(project=project).order_by('-pk')
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        request.data['project'] = project.id
        serializer = SubmissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "DELETE"])
def project_submission(request, project_id, submission_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        submission = Submission.objects.get(project=project, pk=submission_id)
    except Submission.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SubmissionSerializer(submission)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = SubmissionSerializer(submission, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        submission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

"""
Project Submission Test API endpoints
"""

@api_view(["GET", "POST"])
def project_submission_tests(request, project_id, submission_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        submission = Submission.objects.get(project=project, pk=submission_id)
    except Submission.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        tests = TestResult.objects.filter(submission=submission).order_by('-pk')
        serializer = TestResultSerializer(tests, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        request.data['submission'] = submission.id
        serializer = TestResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "DELETE"])
def project_submission_test(request, project_id, submission_id, test_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        submission = Submission.objects.get(project=project, pk=submission_id)
    except Submission.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        test = TestResult.objects.get(submission=submission, pk=test_id)
    except TestResult.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TestResultSerializer(test)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = TestResultSerializer(test, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

"""
Project Reference API endpoints
"""

@api_view(["GET", "POST"])
def project_references(request, project_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    queries = create_reference_query(project, request.query_params)

    if request.method == 'GET':
        reference_sets = project.reference_sets.filter(**queries).order_by('-pk')
        serializer = ReferenceSetSerializer(reference_sets, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        request.data['project'] = project.id
        serializer = ReferenceSetSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError as error:
                return Response(str(error), status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "DELETE"])
def project_reference(request, project_id, reference_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        reference_set = project.reference_sets.get(pk=reference_id)
    except ReferenceSet.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ReferenceSetSerializer(reference_set)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ReferenceSetSerializer(reference_set, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError as error:
                return Response(str(error), status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        reference_set.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

"""
Reference Tests API endpoints
"""

@api_view(["GET", "POST"])
def project_reference_tests(request, project_id, reference_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        reference_set = project.reference_sets.get(pk=reference_id)
    except ReferenceSet.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        query = {}
        for key, value in request.query_params.items():
            query[key] = value#.replace('%20', " ")
        test_references = reference_set.test_references.filter(**query).order_by("-pk")
        serializer = TestReferenceSerializer(test_references, many=True)
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        request.data['reference_set'] = reference_set.id
        serializer = TestReferenceSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
            except IntegrityError as error:
                return Response(str(error), status.HTTP_400_BAD_REQUEST)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["GET", "PUT", "PATCH", "DELETE"])
def project_reference_test(request, project_id, reference_id, test_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        reference_set = project.reference_sets.get(pk=reference_id)
    except ReferenceSet.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    try:
        test_references = reference_set.test_references.get(pk=test_id)
    except TestReference.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TestReferenceSerializer(test_references)
        return Response(serializer.data)

    elif request.method == 'PUT':
        request.data['reference_set'] = reference_set.id
        serializer = TestReferenceSerializer(test_references, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'PATCH':
        # TODO: should we introduce a special serializer here?
        test_references.update_references(
            request.data['references'],
            request.data['default_source'])
        try:
            test_references.save()
            return Response({}, status=status.HTTP_200_OK)
        except Exception as err:
            return Response(str(err), status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        test_references.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

"""
DEBUGGING
"""

@api_view(["GET"])
def WIPE_DATABASE(request):
    for model in [Project, ProjectSubmissionProperty, Submission, TestResult, ReferenceSet, TestReference]:
        model.objects.all().delete()
    return Response({}, status.HTTP_200_OK)