
from django.db import IntegrityError
from django.http import Http404
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics

from dtf.serializers import ProjectSerializer
from dtf.serializers import TestResultSerializer
from dtf.serializers import ReferenceSetSerializer
from dtf.serializers import TestReferenceSerializer
from dtf.serializers import SubmissionSerializer
from dtf.serializers import ProjectSubmissionPropertySerializer
from dtf.serializers import WebhookSerializer
from dtf.serializers import WebhookLogEntrySerializer

from dtf.models import TestResult, Project, ReferenceSet, TestReference, Submission, ProjectSubmissionProperty, Webhook
from dtf.functions import get_project_by_id_or_slug, create_reference_query

def get_project_or_404(project_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        raise Http404
    return project

def get_child_or_404(objects, **kwargs):
    try:
        obj = objects.get(**kwargs)
    except ObjectDoesNotExist:
        raise Http404
    return obj

#
# Project API endpoints
#
class ProjectList(generics.ListCreateAPIView):
    queryset = Project.objects.order_by('-pk')
    serializer_class = ProjectSerializer

class ProjectDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_url_kwarg = 'id'

    def get_object(self):
        return get_project_or_404(self.kwargs['id'])

#
# Project Submission Properties API endpoints
#

class ProjectSubmissionPropertyList(generics.ListCreateAPIView):
    serializer_class = ProjectSubmissionPropertySerializer

    def get_queryset(self):
        project = get_project_or_404(self.kwargs['project_id'])
        return project.properties.order_by('-pk')

    def create(self, request, *args, **kwargs):
        request.data['project'] = get_project_or_404(self.kwargs['project_id']).id
        return super().create(request, *args, **kwargs)

class ProjectSubmissionPropertyDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectSubmissionPropertySerializer
    lookup_url_kwarg = 'property_id'

    def get_queryset(self):
        project = get_project_or_404(self.kwargs['project_id'])
        return project.properties.all()

#
# Project Webhook API endpoints
#

class ProjectWebhookList(generics.ListCreateAPIView):
    serializer_class = WebhookSerializer

    def get_queryset(self):
        project = get_project_or_404(self.kwargs['project_id'])
        return project.webhooks.order_by('-pk')

    def create(self, request, *args, **kwargs):
        request.data['project'] = get_project_or_404(self.kwargs['project_id']).id
        return super().create(request, *args, **kwargs)

class ProjectWebhookDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WebhookSerializer
    lookup_url_kwarg = 'webhook_id'

    def get_queryset(self):
        project = get_project_or_404(self.kwargs['project_id'])
        return project.webhooks.all()

class ProjectWebhookLogList(generics.ListAPIView):
    serializer_class = WebhookLogEntrySerializer

    def get_queryset(self):
        project = get_project_or_404(self.kwargs['project_id'])
        webhook = get_child_or_404(project.webhooks, pk=self.kwargs['webhook_id'])
        return webhook.logs.all()

#
# Project Submission API endpoints
#

@api_view(["GET", "POST"])
def project_submissions(request, project_id):
    project = get_project_by_id_or_slug(project_id)
    if project is None:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        submissions = Submission.objects.filter(project=project).order_by('-pk')
        serializer = SubmissionSerializer(submissions, many=True, context={"request": request})
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        request.data['project'] = project.id
        serializer = SubmissionSerializer(data=request.data, context={"request": request})
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
        serializer = SubmissionSerializer(submission, context={"request": request})
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = SubmissionSerializer(submission, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        submission.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

#
# Project Submission Test API endpoints
#

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
        serializer = TestResultSerializer(tests, many=True, context={"request": request})
        return Response(serializer.data, status.HTTP_200_OK)

    elif request.method == 'POST':
        request.data['submission'] = submission.id
        serializer = TestResultSerializer(data=request.data, context={"request": request})
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
        serializer = TestResultSerializer(test, context={"request": request})
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = TestResultSerializer(test, data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        test.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

#
# Project Reference API endpoints
#

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

#
# Reference Tests API endpoints
#

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

#
# DEBUGGING
#

@api_view(["GET"])
def WIPE_DATABASE(request):
    for model in [Project, ProjectSubmissionProperty, Submission, TestResult, ReferenceSet, TestReference]:
        model.objects.all().delete()
    return Response({}, status.HTTP_200_OK)