from django.shortcuts import render, get_object_or_404
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.urls import reverse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from dtf.serializers import ProjectSerializer
from dtf.serializers import TestResultSerializer
from dtf.serializers import TestReferenceSerializer
from dtf.serializers import SubmissionSerializer
from dtf.models import TestResult, Project, TestReference, Submission
from dtf.functions import create_view_data_from_test_references
from dtf.forms import NewProjectForm

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

def view_project_details(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    submissions = Submission.objects.filter(project=project)
    return render(request, 'dtf/project_details.html', {
        'project':project,
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
GET API endpoints
"""

@api_view(["GET"])
def get_submission_by_id(request, submission_id):
    """
    Returns a list of test results assigned to the submission with the given id
    """
    submission = get_object_or_404(Submission, pk=submission_id)
    data = submission.tests.all()
    serializer = TestResultSerializer(data, many=True)
    return Response(serializer.data, status.HTTP_200_OK)

@api_view(["GET"])
def get_projects(request):
    """
    Returns a list with all current projects in the database
    """
    projects = Project.objects.order_by('-pk')
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data, status.HTTP_200_OK)

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
POST API endpoints
"""

@api_view(["POST"])
def submit_test_results(request):
    serializer = TestResultSerializer(data=request.data)
    if serializer.is_valid():
        # we just get or create the reference object here
        test_reference, _ = TestReference.objects.get_or_create(
            project=serializer.validated_data['submission'].project,
            test_name=serializer.validated_data['name']
        )
        # we do NOT automatically set the posted test as a reference
        # no matter if the reference is set yet or not. just save it
        test_reference.save()

        created_test_result = serializer.save()
        return Response({'test_result_id':created_test_result.pk}, status.HTTP_200_OK)
    return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def create_project(request):
    """Looks for a 'name' and 'slug' fields in the sent data. If both are valid, creates a \
        new project and returns the id of the project

    :param request: The request object that is sent to the view

    :raises [HTTP_400_BAD_REQUEST]: When no 'name' or 'slug' field is found in the post data

    :return: Returns a json object containing the id of the created project
        If the project id is 'None' the project slug was invalid or not not unique.
        No project was created.
    """
    serializer = ProjectSerializer(data=request.data)
    if serializer.is_valid():
        try:
            created_project = serializer.save()
        except IntegrityError:
            # the UNIQUE contraint has failed, a project with this name already exists
            return Response({'project_id':None}, status.HTTP_200_OK)
        return Response({'project_id':created_project.id}, status.HTTP_200_OK)
    return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
def create_submission(request):
    """
    Creates a new submission with incrementing IDs

    Requires a project_id oder project_name to assign the submission to a project
    """
    serializer = SubmissionSerializer(data=request.data)
    if serializer.is_valid():
        submission = serializer.save()
        return Response({'id':submission.pk}, status.HTTP_200_OK)
    return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

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