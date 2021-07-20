
import copy

from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.dateparse import parse_duration
from django.contrib.auth.models import User

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework import views

from dtf.serializers import UserSerializer
from dtf.serializers import ProjectSerializer
from dtf.serializers import MembershipSerializer
from dtf.serializers import TestResultSerializer
from dtf.serializers import ReferenceSetSerializer
from dtf.serializers import TestReferenceSerializer
from dtf.serializers import SubmissionSerializer
from dtf.serializers import ProjectSubmissionPropertySerializer
from dtf.serializers import WebhookSerializer
from dtf.serializers import WebhookLogEntrySerializer

from dtf.models import TestResult, Membership, Project, ReferenceSet, TestReference, Submission, ProjectSubmissionProperty, Webhook
from dtf.functions import get_project_by_id_or_slug, create_reference_query
from dtf.permissions import ProjectPermission

def get_project_or_404(project_id, queryset=Project.objects):
    project = get_project_by_id_or_slug(project_id, queryset)
    if project is None:
        raise Http404
    return project

def get_child_or_404(objects, **kwargs):
    try:
        obj = objects.get(**kwargs)
    except ObjectDoesNotExist:
        raise Http404
    return obj

class ProjectAPIViewMixin():
    project_lookup_url_kwarg = 'project_id'

    def get_project(self):
        return get_project_or_404(self.kwargs[self.project_lookup_url_kwarg])

#
# User API endpoints
#
class UserList(generics.ListAPIView):
    queryset = User.objects.order_by('pk')
    serializer_class = UserSerializer

class UserDetail(generics.RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_url_kwarg = 'id'

#
# Project API endpoints
#
class ProjectList(generics.ListCreateAPIView):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return self.request.user.projects.order_by('-pk')

    def perform_create(self, serializer):
        super().perform_create(serializer)
        serializer.instance.memberships.create(user=self.request.user, role='owner')

class ProjectDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    queryset = Project.objects.all()
    permission_classes = [ProjectPermission]
    serializer_class = ProjectSerializer
    lookup_url_kwarg = 'id'
    project_lookup_url_kwarg = 'id'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_project_or_404(self.kwargs[self.lookup_url_kwarg], queryset)
        self.check_object_permissions(self.request, obj)
        return obj

#
# Project Members API endpoints
#
class ProjectMemberList(generics.ListCreateAPIView, ProjectAPIViewMixin):
    serializer_class = MembershipSerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        return self.get_project().memberships.order_by('-pk')

    def create(self, request, *args, **kwargs):
        request.data['project'] = self.get_project().id
        return super().create(request, *args, **kwargs)

class ProjectMemberDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    serializer_class = MembershipSerializer
    permission_classes = [ProjectPermission]
    lookup_url_kwarg = 'member_id'

    def get_queryset(self):
        return self.get_project().memberships.order_by('-pk')

#
# Project Submission Properties API endpoints
#

class ProjectSubmissionPropertyList(generics.ListCreateAPIView, ProjectAPIViewMixin):
    serializer_class = ProjectSubmissionPropertySerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        return self.get_project().properties.order_by('-pk')

    def create(self, request, *args, **kwargs):
        request.data['project'] = self.get_project().id
        return super().create(request, *args, **kwargs)

class ProjectSubmissionPropertyDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    serializer_class = ProjectSubmissionPropertySerializer
    permission_classes = [ProjectPermission]
    lookup_url_kwarg = 'property_id'

    def get_queryset(self):
        return self.get_project().properties.all()

#
# Project Webhook API endpoints
#

class ProjectWebhookList(generics.ListCreateAPIView, ProjectAPIViewMixin):
    serializer_class = WebhookSerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        return self.get_project().webhooks.order_by('-pk')

    def create(self, request, *args, **kwargs):
        request.data['project'] = self.get_project().id
        return super().create(request, *args, **kwargs)

class ProjectWebhookDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    serializer_class = WebhookSerializer
    permission_classes = [ProjectPermission]
    lookup_url_kwarg = 'webhook_id'

    def get_queryset(self):
        return self.get_project().webhooks.all()

class ProjectWebhookLogList(generics.ListAPIView, ProjectAPIViewMixin):
    serializer_class = WebhookLogEntrySerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        webhook = get_child_or_404(self.get_project().webhooks, pk=self.kwargs['webhook_id'])
        return webhook.logs.all()

#
# Project Submission API endpoints
#

class ProjectSubmissionList(generics.ListCreateAPIView, ProjectAPIViewMixin):
    serializer_class = SubmissionSerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        return self.get_project().submissions.filter(**self.request.query_params.dict()).order_by('-pk')

    def create(self, request, *args, **kwargs):
        project = self.get_project()
        request.data['project'] = project.id
        unique_key = request.query_params.get('unique_key')
        info = request.data.get('info')
        if unique_key is not None and info is not None and unique_key in info:
            query = {
                f'info__{unique_key}': info[unique_key]
            }

            with transaction.atomic():
                try:
                    submission = project.submissions.get(**query)
                    return Response("Submission for the unique key does already exist", status.HTTP_409_CONFLICT)
                except ObjectDoesNotExist:
                    return super().create(request, *args, **kwargs)

        return super().create(request, *args, **kwargs)

class ProjectSubmissionDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    serializer_class = SubmissionSerializer
    permission_classes = [ProjectPermission]
    lookup_url_kwarg = 'submission_id'

    def get_queryset(self):
        return self.get_project().submissions.all()

class ProjectTestResultList(generics.ListAPIView, ProjectAPIViewMixin):
    serializer_class = TestResultSerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        return TestResult.objects.filter(submission__project__id=self.get_project().id).all().order_by('-pk')

class ProjectTestResultDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    serializer_class = TestResultSerializer
    permission_classes = [ProjectPermission]
    lookup_url_kwarg = 'test_id'

    def get_queryset(self):
        return TestResult.objects.filter(submission__project__id=self.get_project().id).all()

#
# Project Submission Test API endpoints
#

class ProjectSubmissionTestResultList(generics.ListCreateAPIView, ProjectAPIViewMixin):
    serializer_class = TestResultSerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        submission = get_child_or_404(self.get_project().submissions, pk=self.kwargs['submission_id'])
        return submission.tests.order_by('-pk')

    def create(self, request, *args, **kwargs):
        request.data['submission'] = get_child_or_404(self.get_project().submissions, pk=self.kwargs['submission_id']).id
        return super().create(request, *args, **kwargs)

class ProjectSubmissionTestResultDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    serializer_class = TestResultSerializer
    permission_classes = [ProjectPermission]
    lookup_url_kwarg = 'test_id'

    def get_queryset(self):
        submission = get_child_or_404(self.get_project().submissions, pk=self.kwargs['submission_id'])
        return submission.tests.all()

#
# Project Reference API endpoints
#

class ProjectReferenceSetList(generics.ListCreateAPIView, ProjectAPIViewMixin):
    serializer_class = ReferenceSetSerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        project = self.get_project()
        queries = create_reference_query(project, self.request.query_params)
        return project.reference_sets.filter(**queries).order_by('-pk')

    def create(self, request, *args, **kwargs):
        request.data['project'] = self.get_project().id
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as error:
            return Response(str(error), status.HTTP_400_BAD_REQUEST)

class ProjectReferenceSetDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    serializer_class = ReferenceSetSerializer
    permission_classes = [ProjectPermission]
    lookup_url_kwarg = 'reference_id'

    def get_queryset(self):
        return self.get_project().reference_sets.all()

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except IntegrityError as error:
            return Response(str(error), status.HTTP_400_BAD_REQUEST)

#
# Reference Tests API endpoints
#

class ProjectReferenceSetTestReferenceList(generics.ListCreateAPIView, ProjectAPIViewMixin):
    serializer_class = TestReferenceSerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        reference_set = get_child_or_404(self.get_project().reference_sets, pk=self.kwargs['reference_id'])
        return reference_set.test_references.filter(**self.request.query_params.dict()).order_by('-pk')

    def create(self, request, *args, **kwargs):
        request.data['reference_set'] = get_child_or_404(self.get_project().reference_sets, pk=self.kwargs['reference_id']).id
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as error:
            return Response(str(error), status.HTTP_400_BAD_REQUEST)

class ProjectReferenceSetTestReferenceDetail(generics.RetrieveUpdateDestroyAPIView, ProjectAPIViewMixin):
    serializer_class = TestReferenceSerializer
    permission_classes = [ProjectPermission]
    lookup_url_kwarg = 'test_id'

    def get_queryset(self):
        reference_set = get_child_or_404(self.get_project().reference_sets, pk=self.kwargs['reference_id'])
        return reference_set.test_references.all()

    def update(self, request, *args, **kwargs):
        try:
            return super().update(request, *args, **kwargs)
        except IntegrityError as error:
            return Response(str(error), status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        test_references = self.get_object()

        # TODO: should we introduce a special serializer here?
        test_references.update_references(
            request.data['references'],
            request.data['default_source'])
        try:
            test_references.save()
            return Response({}, status=status.HTTP_200_OK)
        except Exception as err:
            return Response(str(err), status=status.HTTP_400_BAD_REQUEST)

class TestMeasurementHistory(views.APIView, ProjectAPIViewMixin):
    permission_classes = [ProjectPermission]
    permission_model = TestResult

    def get(self, request, project_id, submission_id, test_id):
        project = self.get_project()
        submission = get_object_or_404(Submission, pk=submission_id)
        test_result = get_object_or_404(TestResult, pk=test_id)

        if test_result.submission != submission:
            return Response(str("The test does not belong to this submission"), status=status.HTTP_400_BAD_REQUEST)
        if submission.project != project:
            return Response(str("The test does not belong to this project"), status=status.HTTP_400_BAD_REQUEST)

        measurement_name = request.query_params.get("measurement_name")

        limit = request.query_params.get("limit")
        try:
            if limit:
                limit = int(limit)
        except:
            limit = None

        info_query = {}
        submission_info_query = {}
        for prop in project.properties.all():
            if prop.influence_reference:
                prop_value = submission.info.get(prop.name)
                if not prop_value is None:
                    info_query['info__' + prop.name] = prop_value
                    submission_info_query['submission__info__' + prop.name] = prop_value

        # submissions = project.submissions.filter(**queries).order_by("-created")

        historic_tests = TestResult.objects.filter(
            name=test_result.name,
            submission__project__id=project.id,
            **submission_info_query
        ).order_by("-created")

        if limit:
            historic_tests = historic_tests[:limit]
        else:
            historic_tests = historic_tests.all()

        data = []
        # for submission in submissions.all():
        #     test = submission.tests.get(name=test_result.name)
        #     if not test: continue
        for test in historic_tests:
            entry = {
                'value_source' : test.id,
                'date' : test.created
            }
            for measurement in test.results:
                if measurement['name'] == measurement_name:
                    entry['value'] = copy.deepcopy(measurement['value'])
                    entry['reference'] = copy.deepcopy(measurement['reference'])
                    entry['status'] = copy.deepcopy(measurement['status'])
                    entry['reference_source'] = measurement.get('reference_source')
                    break
            data.append(entry)

        return Response(data, status.HTTP_200_OK)
