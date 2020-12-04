from django.shortcuts import render, get_object_or_404
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.forms import inlineformset_factory

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from dtf.serializers import ProjectSerializer
from dtf.serializers import TestResultSerializer
from dtf.serializers import TestReferenceSerializer
from dtf.serializers import SubmissionSerializer
from dtf.serializers import ProjectSubmissionPropertySerializer
from dtf.models import TestResult, Project, TestReference, Submission, ProjectSubmissionProperty
from dtf.functions import create_view_data_from_test_references, get_project_by_id_or_slug
from dtf.forms import NewProjectForm, ProjectSettingsForm, ProjectSubmissionPropertyForm

"""
User views
"""

def frontpage(request):
    results = TestResult.objects.order_by('-first_submitted')[:5]
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
    PropertiesFormset = inlineformset_factory(Project, ProjectSubmissionProperty, fields=('name', 'required', 'display', 'display_replace', 'display_as_link', 'influence_reference'), form=ProjectSubmissionPropertyForm)

    project = get_object_or_404(Project, slug=project_slug)
    properties = ProjectSubmissionProperty.objects.filter(project=project)

    if request.method == 'POST':
        form = ProjectSettingsForm(request.POST, instance=project)
        properties_formset = PropertiesFormset(request.POST, instance=project)
        if form.is_valid() and properties_formset.is_valid():
            form.save()
            properties_formset.save()
    else:
        form = ProjectSettingsForm(instance=project)
        properties_formset = PropertiesFormset(instance=project)

    return render(request, 'dtf/project_settings.html', {
        'project': project,
        'form': form,
        'properties_formset': properties_formset
    })

def view_project_details(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    properties = ProjectSubmissionProperty.objects.filter(project=project)
    submissions = Submission.objects.filter(project=project)
    return render(request, 'dtf/project_details.html', {
        'project':project,
        'properties':properties,
        'submissions':submissions
    })

def view_test_result_details(request, test_id):
    test_result = get_object_or_404(TestResult, pk=test_id)
    project = test_result.submission.project
    # we did try except at this point. with our current method, there is no way that
    # a test result object exists without a corresponding reference object
    # worst case the references are empty, but the object still exists
    references_object = TestReference.objects.get(
        test_name=test_result.name,
        project=project)
    # this can fail if a submission gets assigned another project by hand
    references = references_object.references
    data = create_view_data_from_test_references(
        test_result.results, references)
    nav_data = project.get_nav_data(test_result.name, test_result.submission.id)
    return render(request, 'dtf/test_result_details.html', {
        'project':project,
        'test_name':test_result.name,
        'test_result':test_result,
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
        request.data['project_id'] = project.id
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
        request.data['project_id'] = project.id
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
        request.data['submission_id'] = submission.id
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

@api_view(["GET"])
def get_reference(request, project_slug, test_name):
    """
    Return the references of a test matching the given project slug and test name
    """
    data = TestReference.objects.filter(
        test_name=test_name,
        project__slug=project_slug
    )
    serializer = TestReferenceSerializer(data, many=True)
    return Response(serializer.data, status.HTTP_200_OK)

@api_view(["GET"])
def get_reference_by_test_id(request, test_id):
    """
    Return the references for the test with the given test_id
    """
    try:
        test_result = TestResult.objects.get(id=test_id)
    except TestResult.DoesNotExist:
        return Response({"error":"No test_result with given id found"}, status.HTTP_400_BAD_REQUEST)
    data = TestReference.objects.filter(
        test_name=test_result.name,
        project=test_result.submission.project
    )
    serializer = TestReferenceSerializer(data, many=True)
    return Response(serializer.data, status.HTTP_200_OK)

"""
PUT API endpoints
"""

@api_view(["PUT"])
def update_references(request):
    serializer = TestReferenceSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({}, status.HTTP_200_OK)
    return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

"""
DEBUGGING
"""

@api_view(["GET"])
def WIPE_DATABASE(request):
    for model in [Project, Submission, TestResult, TestReference]:
        model.objects.all().delete()
    return Response({}, status.HTTP_200_OK)