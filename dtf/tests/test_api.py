"""
Module containing the API unit tests

Tests:
create project
get_projects
submit_test_results
update_references
"""

import json
import copy
import datetime
import time
from urllib.parse import urlencode

from rest_framework import status

from django.test import TestCase, Client
from django.urls import reverse
from django.utils.text import slugify
from django.db import transaction
from django.contrib.auth.models import User

from dtf.models import Project, Membership, TestResult, ReferenceSet, TestReference, Submission, ProjectSubmissionProperty, Webhook
from dtf.serializers import ProjectSerializer
from dtf.serializers import TestResultSerializer
from dtf.serializers import ProjectSubmissionPropertySerializer
from dtf.serializers import SubmissionSerializer
from dtf.serializers import ReferenceSetSerializer
from dtf.serializers import TestReferenceSerializer
from dtf.serializers import WebhookSerializer
from dtf.serializers import MembershipSerializer
from dtf.serializers import UserSerializer

client = Client()

class ApiTestCase(TestCase):

    def setUp(self):
        self.testuser = User.objects.create_user(username='test')
        client.force_login(self.testuser)

    def post(self, url, payload):
        response = client.post(
            url,
            json.dumps(payload),
            content_type='application/json'
        )
        return response, response.data

    def put(self, url, payload):
        response = client.put(
            url,
            json.dumps(payload),
            content_type='application/json'
        )
        return response, response.data

    def patch(self, url, payload):
        response = client.patch(
            url,
            json.dumps(payload),
            content_type='application/json'
        )
        return response, response.data

    def create_project(self, name, slug=None):
        if slug is None:
            slug = slugify(name)
        valid_payload = {
            'name':name,
            'slug':slug
        }
        return self.post(reverse('api_projects'), valid_payload)

    def create_submission(self, project_id=None, info=None, unique_key=None):
        payload = {}
        if info is not None:
            payload['info'] = info

        url = reverse('api_project_submissions', kwargs={'project_id' : project_id})
        if unique_key is not None:
            url += "?"
            url += urlencode({'unique_key': unique_key})

        return self.post(url, payload)

# Create your tests here.
class ProjectsApiTest(ApiTestCase):
    """ Test module for Project model interaction with API """
    def setUp(self):
        super().setUp()
        self.invalid_payload = {
            'not_a_name':'no name given'
        }

    def test_create(self):
        # Test success
        response, data = self.create_project("Test Project", "test-project")
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], "Test Project")
        self.assertEqual(data['slug'], "test-project")

        # Test invalid payload
        response, data = self.post(reverse('api_projects'), self.invalid_payload)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Different name, same slug
        response, data = self.create_project("New Test Project", "test-project")
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test same name, different slug
        response, data = self.create_project("Test Project", "other-slug")
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test invalid slug
        response, data = self.create_project("Test Project", "Invalid Slug")
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_force_create_date(self):
        created = datetime.datetime(year=2020, month=11, day=17, hour=14, minute=44, tzinfo=datetime.timezone(+datetime.timedelta(hours=1)))
        payload = {
            'name': "Test Project",
            'slug': "test-project",
            'created': created.isoformat()
        }
        response, data = self.post(reverse('api_projects'), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.first()
        self.assertEqual(project.created, created)

    def test_get(self):
        _ = self.create_project('Test Project 1')
        _ = self.create_project('Test Project 2')
        _ = self.create_project('Test/Project#?3')
        response = client.get(reverse('api_projects'))
        projects = Project.objects.order_by('-pk')
        serializer = ProjectSerializer(projects, many=True, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ProjectApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.project_1_name = "Test Project 1"
        self.project_2_name = "Test/Project#?2"
        self.project_1_slug = "test-project-1"
        self.project_2_slug = "test-project-2"
        _, data = self.create_project(self.project_1_name, self.project_1_slug)
        self.project_1_id = data['id']
        _, data = self.create_project(self.project_2_name, self.project_2_slug)
        self.project_2_id = data['id']

        self.project_1 = Project.objects.get(id=self.project_1_id)
        self.project_2 = Project.objects.get(id=self.project_2_id)

    def test_get_project_id(self):
        response = client.get(reverse('api_project', kwargs={'id' : self.project_1_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSerializer(self.project_1, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

        response = client.get(reverse('api_project', kwargs={'id' : self.project_2_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSerializer(self.project_2, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

    def test_get_project_slug(self):
        response = client.get(reverse('api_project', kwargs={'id' : self.project_1_slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSerializer(self.project_1, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

        response = client.get(reverse('api_project', kwargs={'id' : self.project_2_slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSerializer(self.project_2, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

    def test_get_project_invalid(self):
        response = client.get(reverse('api_project', kwargs={'id' : "does-not-exist"}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify_project(self):
        response = client.get(reverse('api_project', kwargs={'id' : self.project_1_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_name = "Project 1 New Name"
        response.data['name'] = new_name
        response = client.put(reverse('api_project', kwargs={'id' : self.project_1_id}), data=response.data, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        project_1 = Project.objects.get(id=self.project_1_id)
        self.assertEqual(project_1.name, new_name)

    def test_delete_project(self):
        response = client.delete(reverse('api_project', kwargs={'id' : self.project_1_id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 1)

class ProjectMembersApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        self.project = Project.objects.get(id=data['id'])
        self.url = reverse('api_project_members', kwargs={'project_id' : self.project_id})
        self.user_1 = User.objects.create_user('user1')
        self.user_2 = User.objects.create_user('user2')

    def test_create(self):
        min_payload = {
            'user' : self.user_1.id,
        }
        response, data = self.post(self.url, min_payload)
        self.assertEqual(self.project.members.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['user'], UserSerializer(self.user_1).data)
        self.assertEqual(data['role'], "guest")

        full_payload = {
            'user' : UserSerializer(self.user_2).data,
            'role' : "owner"
        }
        response, data = self.post(self.url, full_payload)
        self.assertEqual(self.project.members.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id'], 2)
        self.assertEqual(data['user'], UserSerializer(self.user_2).data)
        self.assertEqual(data['role'], "owner")

    def test_get(self):
        self.post(self.url, {'user' : self.user_1.id})
        self.post(self.url, {'user' : self.user_2.id})
        response = client.get(self.url)
        members = Membership.objects.order_by('-pk')
        serializer = MembershipSerializer(members, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ProjectMemberApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        create_url = reverse('api_project_members', kwargs={'project_id' : self.project_id})
        self.user_1 = User.objects.create_user('user1')
        self.user_2 = User.objects.create_user('user2')

        response, data = self.post(create_url, {'user' : self.user_1.id})
        self.member_1_id = data['id']
        self.url_1 = reverse('api_project_member', kwargs={'project_id' : self.project_id, 'member_id' : self.member_1_id})
        self.member_1 = Membership.objects.get(id=self.member_1_id)

        response, data = self.post(create_url, {'user' : self.user_2.id})
        self.member_2_id = data['id']
        self.url_2 = reverse('api_project_member', kwargs={'project_id' : self.project_id, 'member_id' : self.member_2_id})
        self.member_2 = Membership.objects.get(id=self.member_2_id)

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = MembershipSerializer(self.member_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = MembershipSerializer(self.member_2)
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_member', kwargs={'project_id' : "invalid", 'member_id' : self.member_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_member', kwargs={'project_id' : self.project_id, 'member_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_role = "owner"
        response.data['role'] = new_role
        response, data = self.put(self.url_1, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        member_1 = Membership.objects.get(id=self.member_1_id)
        self.assertEqual(member_1.role, new_role)

    def test_delete(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Membership.objects.count(), 1)

class ProjectSubmissionPropertiesApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        self.url = reverse('api_project_submission_properties', kwargs={'project_id' : self.project_id})

    def test_create(self):
        min_payload = {
            'name' : "Property 1",
        }
        response, data = self.post(self.url, min_payload)
        self.assertEqual(ProjectSubmissionProperty.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], min_payload['name'])

        full_payload = {
            'name' : "Property 2",
            'required' : True,
            'display' : False,
            'display_replace' : "New {VALUE}",
            'display_as_link' : True,
            'influence_reference' : True,
        }
        response, data = self.post(self.url, full_payload)
        self.assertEqual(ProjectSubmissionProperty.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id'], 2)
        self.assertEqual(data['name'], full_payload['name'])
        self.assertEqual(data['required'], full_payload['required'])
        self.assertEqual(data['display'], full_payload['display'])
        self.assertEqual(data['display_replace'], full_payload['display_replace'])
        self.assertEqual(data['display_as_link'], full_payload['display_as_link'])
        self.assertEqual(data['influence_reference'], full_payload['influence_reference'])

    def test_get(self):
        self.post(self.url, {'name' : "Property 1"})
        self.post(self.url, {'name' : "Property 2"})
        response = client.get(self.url)
        properties = ProjectSubmissionProperty.objects.order_by('-pk')
        serializer = ProjectSubmissionPropertySerializer(properties, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ProjectSubmissionPropertyApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        create_url = reverse('api_project_submission_properties', kwargs={'project_id' : self.project_id})

        response, data = self.post(create_url, {'name' : "Property 1"})
        self.property_1_id = data['id']
        self.url_1 = reverse('api_project_submission_property', kwargs={'project_id' : self.project_id, 'property_id' : self.property_1_id})
        self.property_1 = ProjectSubmissionProperty.objects.get(id=self.property_1_id)

        response, data = self.post(create_url, {'name' : "Property 2"})
        self.property_2_id = data['id']
        self.url_2 = reverse('api_project_submission_property', kwargs={'project_id' : self.project_id, 'property_id' : self.property_2_id})
        self.property_2 = ProjectSubmissionProperty.objects.get(id=self.property_2_id)

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSubmissionPropertySerializer(self.property_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSubmissionPropertySerializer(self.property_2)
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_submission_property', kwargs={'project_id' : "invalid", 'property_id' : self.property_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_submission_property', kwargs={'project_id' : self.project_id, 'property_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_name = "Property 1 New Name"
        response.data['name'] = new_name
        response, data = self.put(self.url_1, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        property_1 = ProjectSubmissionProperty.objects.get(id=self.property_1_id)
        self.assertEqual(property_1.name, new_name)

    def test_delete_project(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 1)

class SubmissionsApiTest(ApiTestCase):
    """ Test module for submissions"""

    def setUp(self):
        super().setUp()
        self.project_name = "Submission Project"
        self.project_slug = "submission-project"
        _, data = self.create_project(self.project_name, self.project_slug)
        self.project_id = data['id']

        self.invalid_project_slug = "does-not-exist"
        self.invalid_project_id = "123"

        self.url = reverse('api_project_submissions', kwargs={'project_id' : self.project_id})

    def test_create(self):
        # Create with project slug
        response, data = self.create_submission(project_id=self.project_slug)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(data['id'], 1)

        response, _ = self.create_submission(project_id=self.invalid_project_slug)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Submission.objects.count(), 1)

        # Create with project ID
        response, data = self.create_submission(project_id=self.project_id)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 2)
        self.assertEqual(data['id'], 2)

        response, _ = self.create_submission(project_id=self.invalid_project_id)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Submission.objects.count(), 2)

    def test_create_with_info(self):
        response, data = self.create_submission(project_id=self.project_id, info={"Key": "Value"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(data['id'], 1)

    def test_create_with_unique_info(self):
        response, data = self.create_submission(project_id=self.project_id, info={"Key": "123", "Unique Key": "456"}, unique_key="Unique Key")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(data['id'], 1)

        response, data = self.create_submission(project_id=self.project_id, info={"Key": "123", "Unique Key": "456"}, unique_key="Unique Key")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Submission.objects.count(), 1)

        response, data = self.create_submission(project_id=self.project_id, info={"Key": "123", "Unique Key": "789"}, unique_key="Unique Key")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 2)
        self.assertEqual(data['id'], 2)

    def test_create_with_required_info(self):
        create_property_url = reverse('api_project_submission_properties', kwargs={'project_id' : self.project_id})
        response, data = self.post(create_property_url, {'name' : "Property1", "required" : True})

        # Create with only required info
        response, data = self.create_submission(project_id=self.project_id, info={"Property1": "Value"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(data['id'], 1)

        # Create with additional info
        response, data = self.create_submission(project_id=self.project_id, info={"Property1": "Value", "Property2": "Other Value"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 2)
        self.assertEqual(data['id'], 2)

        # Create with missing info
        response, data = self.create_submission(project_id=self.project_id, info={"Property2": "Other Value"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Submission.objects.count(), 2)

    def test_create_force_create_date(self):
        created = datetime.datetime(year=2020, month=11, day=17, hour=14, minute=44, tzinfo=datetime.timezone(+datetime.timedelta(hours=1)))
        payload = {
            'created': created.isoformat()
        }
        response, data = self.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Submission.objects.count(), 1)
        submission = Submission.objects.first()
        self.assertEqual(submission.created, created)

    def test_get(self):
        self.create_submission(project_id=self.project_id, info={"Key": "Value"})
        self.create_submission(project_id=self.project_id, info={"Key": "Value"})
        response = client.get(self.url)
        submissions = Submission.objects.order_by('-pk')
        serializer = SubmissionSerializer(submissions, many=True, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_query(self):
        self.create_submission(project_id=self.project_id, info={"Key": "Value 1"})
        self.create_submission(project_id=self.project_id, info={"Key": "Value 1"})
        self.create_submission(project_id=self.project_id, info={"Key": "Value 2"})

        response = client.get(self.url, {"info__Key": "Value 1"})
        submissions = Submission.objects.filter(info__Key="Value 1").order_by('-pk')
        serializer = SubmissionSerializer(submissions, many=True, context={"request": response.wsgi_request})
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get(self.url, {"info__Key": "Value 2"})
        submissions = Submission.objects.filter(info__Key="Value 2").order_by('-pk')
        serializer = SubmissionSerializer(submissions, many=True, context={"request": response.wsgi_request})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get(self.url, {"info__Key": "ValueDoesNotExit"})
        self.assertEqual(len(response.data), 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get(self.url, {"info__KeyDoesNotExist": "Value 1"})
        self.assertEqual(len(response.data), 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class SubmissionApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']

        _, data = self.create_submission(project_id=self.project_id, info={"Key": "Value"})
        self.submission_1_id = data['id']
        self.url_1 = reverse('api_project_submission', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_1_id})
        self.submission_1 = Submission.objects.get(id=self.submission_1_id)

        _, data = self.create_submission(project_id=self.project_id, info={"Key": "Value"})
        self.submission_2_id = data['id']
        self.url_2 = reverse('api_project_submission', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_2_id})
        self.submission_2 = Submission.objects.get(id=self.submission_2_id)

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = SubmissionSerializer(self.submission_1, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = SubmissionSerializer(self.submission_2, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_submission', kwargs={'project_id' : "invalid", 'submission_id' : self.submission_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_submission', kwargs={'project_id' : self.project_id, 'submission_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_info = copy.deepcopy(response.data['info'])
        new_info["Key"] = "Other Value"
        new_info["Key2"] = "Second Value"
        response.data['info'] = new_info
        response, data = self.put(self.url_1, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        submission_1 = Submission.objects.get(id=self.submission_1_id)
        self.assertEqual(submission_1.info, new_info)

    def test_delete_project(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 1)

class TestResultsApiTest(ApiTestCase):
    """ Test module for submitting test results via the API """

    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id = data['id']

        self.url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id})

        self.small_valid_payload = {
            "name": "UNIT_TEST",
            "results":[
                {
                    "name": "parameter1",
                    "value" : {
                        "data" : 5,
                        "type" : "integer"
                    },
                },
            ],
        }

        self.large_valid_payload = {
            "name": "UNIT_TEST",
            "results":[
                {
                    "name": "parameter1",
                    "value" : {
                        "data" : 1,
                        "type" : "integer"
                    },
                },
                {
                    "name": "parameter2",
                    "value" : {
                        "data" : 2,
                        "type" : "float"
                    },
                },
                {
                    "name": "parameter3",
                    "value" : {
                        "data" : 3.4,
                        "type" : "float"
                    },
                },
                {
                    "name": "parameter4",
                    "value" : {
                        "data" : "some value",
                        "type" : "string"
                    },
                },
                {
                    "name": "parameter5",
                    "value" : {
                        "data" : "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAVSURBVBhXY2BQ+/+fAQj+//9V8B8AJIUGjCXQWGcAAAAASUVORK5CYII=",
                        "type" : "image"
                    },
                },
                {
                    "name": "parameter6",
                    "value" : {
                        "data" : {
                            "shape" : [ 2 ],
                            "entries" : [
                                { "data" : 1.0, "type" : "float" },
                                { "data" : 2.0, "type" : "float" },
                            ]
                        },
                        "type" : "ndarray"
                    },
                },
                {
                    "name": "parameter7",
                    "value" : {
                        "data" : {
                            "shape" : [ 2, 3 ],
                            "entries" : [
                                { "data" : 1.0, "type" : "float" },
                                { "data" : 2.0, "type" : "float" },
                                { "data" : 3.0, "type" : "float" },
                                { "data" : 4.0, "type" : "float" },
                                { "data" : 5.0, "type" : "float" },
                                { "data" : 6.0, "type" : "float" },
                            ]
                        },
                        "type" : "ndarray"
                    },
                },
                {
                    "name": "parameter8",
                    "value" : {
                        "data" : "P400DT3H5.5M",
                        "type" : "duration"
                    },
                },
            ],
        }

    def test_create(self):
        response, data = self.post(self.url, self.small_valid_payload)
        self.assertEqual(TestResult.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], self.small_valid_payload['name'])
        self.assertEqual(data['results'][0]["name"], self.small_valid_payload['results'][0]["name"])
        self.assertEqual(data['results'][0]["value"], self.small_valid_payload['results'][0]["value"])

        response, data = self.post(self.url, self.large_valid_payload)
        self.assertEqual(TestResult.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id'], 2)
        self.assertEqual(data['name'], self.large_valid_payload['name'])
        for i in range(len(self.large_valid_payload['results'])):
            self.assertEqual(data['results'][i]["name"], self.large_valid_payload['results'][i]["name"])
            self.assertEqual(data['results'][i]["value"], self.large_valid_payload['results'][i]["value"])

    def test_create_invalid(self):
        missing_name_payload = {
            "results": []
        }
        response, data = self.post(self.url, missing_name_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_payload = {
            "name": "UNIT_TEST",
            "results": [
                {
                    "name": "parameter1",
                }
            ],
        }

        response, data = self.post(self.url, invalid_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_payload["results"][0]["value"] = { 'data' : 'not_a_number', 'type' : 'integer' }
        response, data = self.post(self.url, invalid_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_payload["results"][0]["value"] = { 'data' : 1.23, 'type' : 'integer' }
        response, data = self.post(self.url, invalid_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_payload["results"][0]["value"] = { 'data' : 'not_a_number', 'type' : 'float' }
        response, data = self.post(self.url, invalid_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_payload["results"][0]["value"] = { 'data' : 'not_a_timedelta', 'type' : 'duration' }
        response, data = self.post(self.url, invalid_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_payload["results"][0]["value"] = { 'data' : 1.0, 'type' : 'float' }
        invalid_payload["results"][0]["status"] = 'invalid_status'
        response, data = self.post(self.url, invalid_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        invalid_payload["results"] = {}
        response, data = self.post(self.url, invalid_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_force_create_date(self):
        created = datetime.datetime(year=2020, month=11, day=17, hour=14, minute=44, tzinfo=datetime.timezone(+datetime.timedelta(hours=1)))
        payload = copy.deepcopy(self.small_valid_payload)
        payload['created'] = created.isoformat()
        response, data = self.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestResult.objects.count(), 1)
        test_result = TestResult.objects.first()
        self.assertEqual(test_result.created, created)

    def test_get(self):
        response, data = self.post(self.url, self.small_valid_payload)
        response = client.get(self.url)
        tests = TestResult.objects.order_by('-pk')
        serializer = TestResultSerializer(tests, many=True, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class TestResultApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id = data['id']
        create_url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id})

        response, data = self.post(create_url, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}]})
        self.test_1_id = data['id']
        self.url_1 = reverse('api_project_submission_test', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id, 'test_id' : self.test_1_id})
        self.test_1 = TestResult.objects.get(id=self.test_1_id)

        response, data = self.post(create_url, {'name' : 'Test 2', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}]})
        self.test_2_id = data['id']
        self.url_2 = reverse('api_project_submission_test', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id, 'test_id' : self.test_2_id})
        self.test_2 = TestResult.objects.get(id=self.test_2_id)

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TestResultSerializer(self.test_1, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TestResultSerializer(self.test_2, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_submission_test', kwargs={'project_id' : "invalid", 'submission_id' : self.submission_id, 'test_id' : self.test_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_submission_test', kwargs={'project_id' : self.project_id, 'submission_id' : 123, 'test_id' : self.test_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response = client.get(reverse('api_project_submission_test', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id, 'test_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_name = "Test 1 New Name"
        response.data['name'] = new_name
        new_test_data = {'name' : 'Result2', 'value' : { 'data' : 2, 'type' : 'integer'}}
        response.data['results'].append(new_test_data)
        response, data = self.put(self.url_1, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_1 = TestResult.objects.get(id=self.test_1_id)
        self.assertEqual(test_1.name, new_name)
        self.assertEqual(test_1.results[1]["name"], new_test_data["name"])
        self.assertEqual(test_1.results[1]["value"], new_test_data["value"])

    def test_delete(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TestResult.objects.count(), 1)

class TestResultHistoryApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        property_url = reverse('api_project_submission_properties', kwargs={'project_id' : self.project_id})
        self.post(property_url, {
            'name' : "Property1",
            'required' : True,
            'influence_reference' : True,
        })

        _, data = self.create_submission(project_id=self.project_id, info={"Property1": "Value1", "Property2": "Value1"})
        self.submission_1_id = data['id']
        create_url_1 = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_1_id})
        _, data = self.post(create_url_1, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}]})
        self.test_1_id = data['id']
        self.test_1 = TestResult.objects.get(id=self.test_1_id)

        time.sleep(1e-6) # Wait a microsecond to make sure the next test has another 'created' date
        _, data = self.create_submission(project_id=self.project_id, info={"Property1": "Value1", "Property2": "Value2"})
        self.submission_2_id = data['id']
        create_url_2 = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_2_id})
        _, data = self.post(create_url_2, {'name' : 'Test 1', 'results' : [{'name' : 'Result2', 'value' : { 'data' : 2, 'type' : 'integer'}}]})
        self.test_2_id = data['id']
        self.test_2 = TestResult.objects.get(id=self.test_2_id)

        time.sleep(1e-6) # Wait a microsecond to make sure the next test has another 'created' date
        _, data = self.create_submission(project_id=self.project_id, info={"Property1": "Value1", "Property2": "Value3"})
        self.submission_3_id = data['id']
        create_url_3 = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_3_id})
        _, data = self.post(create_url_3, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 3, 'type' : 'integer'}}]})
        self.test_3_id = data['id']
        self.test_3 = TestResult.objects.get(id=self.test_3_id)

        time.sleep(1e-6) # Wait a microsecond to make sure the next test has another 'created' date
        _, data = self.create_submission(project_id=self.project_id, info={"Property1": "Value2", "Property2": "Value4"})
        self.submission_4_id = data['id']
        create_url_4 = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_4_id})
        _, data = self.post(create_url_4, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 3, 'type' : 'integer'}}]})
        self.test_4_id = data['id']
        self.test_4 = TestResult.objects.get(id=self.test_4_id)

        self.url_1 = reverse('api_project_submission_test_measurement_history', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_1_id, 'test_id' : self.test_1_id})
        self.url_2 = reverse('api_project_submission_test_measurement_history', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_2_id, 'test_id' : self.test_2_id})
        self.url_3 = reverse('api_project_submission_test_measurement_history', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_3_id, 'test_id' : self.test_3_id})
        self.url_4 = reverse('api_project_submission_test_measurement_history', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_4_id, 'test_id' : self.test_4_id})

    def test_get(self):
        expected_data = [{
            'value_source' : self.test_3.id,
            'date' : self.test_3.created,
            'value' : self.test_3.results[0]['value'],
            'reference' : self.test_3.results[0]['reference'],
            'status' : self.test_3.results[0]['status'],
            'reference_source' : self.test_3.results[0].get('reference_source'),
        },
        {
            'value_source' : self.test_2.id,
            'date' : self.test_2.created,
        },
        {
            'value_source' : self.test_1.id,
            'date' : self.test_1.created,
            'value' : self.test_1.results[0]['value'],
            'reference' : self.test_1.results[0]['reference'],
            'status' : self.test_1.results[0]['status'],
            'reference_source' : self.test_1.results[0].get('reference_source'),
        }]

        response = client.get(self.url_1, {"measurement_name": "Result1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

        # same tests in other submissions with same properties should give same results
        response = client.get(self.url_2, {"measurement_name": "Result1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

        response = client.get(self.url_3, {"measurement_name": "Result1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_get_limit(self):
        expected_data = [{
            'value_source' : self.test_3.id,
            'date' : self.test_3.created,
            'value' : self.test_3.results[0]['value'],
            'reference' : self.test_3.results[0]['reference'],
            'status' : self.test_3.results[0]['status'],
            'reference_source' : self.test_3.results[0].get('reference_source'),
        },
        {
            'value_source' : self.test_2.id,
            'date' : self.test_2.created,
        }]

        response = client.get(self.url_1, {"measurement_name": "Result1", "limit" : 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

    def test_empty(self):
        response = client.get(self.url_1, {"measurement_name": "Does not exist"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [{
            'value_source' : self.test_3.id,
            'date' : self.test_3.created
        },
        {
            'value_source' : self.test_2.id,
            'date' : self.test_2.created
        },
        {
            'value_source' : self.test_1.id,
            'date' : self.test_1.created
        }]
        self.assertEqual(response.data, expected_data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_submission_test_measurement_history', kwargs={'project_id' : "invalid", 'submission_id' : self.submission_1_id, 'test_id' : self.test_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_submission_test_measurement_history', kwargs={'project_id' : self.project_id, 'submission_id' : 123, 'test_id' : self.test_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_submission_test_measurement_history', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_1_id, 'test_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class ProjectTestResultsApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id_1 = data['id']
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id_2 = data['id']

        self.url = reverse('api_project_tests', kwargs={'project_id' : self.project_id})

        create_1_url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id_1})
        create_2_url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id_2})

        response, data = self.post(create_1_url, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}]})
        response, data = self.post(create_1_url, {'name' : 'Test 2', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 2, 'type' : 'integer'}}]})
        response, data = self.post(create_2_url, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 3, 'type' : 'integer'}}]})

    def test_get(self):
        response = client.get(self.url)
        tests = TestResult.objects.order_by('-pk')
        serializer = TestResultSerializer(tests, many=True, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class TestResultApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id_1 = data['id']
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id_2 = data['id']

        create_1_url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id_1})
        create_2_url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id_2})

        response, data = self.post(create_1_url, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}]})
        self.test_1_id = data['id']
        self.url_1 = reverse('api_project_test', kwargs={'project_id' : self.project_id, 'test_id' : self.test_1_id})
        self.test_1 = TestResult.objects.get(id=self.test_1_id)

        response, data = self.post(create_2_url, {'name' : 'Test 2', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}]})
        self.test_2_id = data['id']
        self.url_2 = reverse('api_project_test', kwargs={'project_id' : self.project_id, 'test_id' : self.test_2_id})
        self.test_2 = TestResult.objects.get(id=self.test_2_id)

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TestResultSerializer(self.test_1, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TestResultSerializer(self.test_2, context={"request": response.wsgi_request})
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_test', kwargs={'project_id' : "invalid", 'test_id' : self.test_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response = client.get(reverse('api_project_test', kwargs={'project_id' : self.project_id, 'test_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_name = "Test 1 New Name"
        response.data['name'] = new_name
        new_test_data = {'name' : 'Result2', 'value' : { 'data' : 2, 'type' : 'integer'}}
        response.data['results'].append(new_test_data)
        response, data = self.put(self.url_1, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_1 = TestResult.objects.get(id=self.test_1_id)
        self.assertEqual(test_1.name, new_name)
        self.assertEqual(test_1.results[1]["name"], new_test_data["name"])
        self.assertEqual(test_1.results[1]["value"], new_test_data["value"])

    def test_delete(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TestResult.objects.count(), 1)

class ReferenceSetsApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        # Create simple project without properties
        _, data = self.create_project("Test Project 1", "test-project-1")
        self.project_1_id = data['id']
        self.project_1 = Project.objects.get(id=self.project_1_id)
        self.url_1 = reverse('api_project_references', kwargs={'project_id' : self.project_1_id})

        # Create project with some properties
        _, data = self.create_project("Test Project 2", "test-project-2")
        self.project_2_id = data['id']
        self.project_2 = Project.objects.get(id=self.project_2_id)
        self.url_2 = reverse('api_project_references', kwargs={'project_id' : self.project_2_id})
        property_url = reverse('api_project_submission_properties', kwargs={'project_id' : self.project_2_id})
        self.post(property_url, {
            'name' : "Property 1",
            'required' : True,
            'influence_reference' : True,
        })
        self.post(property_url, {
            'name' : "Property 2",
            'required' : True,
            'influence_reference' : True,
        })
        self.post(property_url, {
            'name' : "Property 3",
            'influence_reference' : False,
        })

    def test_create_empty(self):
        response, data = self.post(self.url_1, {'property_values' : {}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReferenceSet.objects.count(), 1)
        self.assertEqual(self.project_1.reference_sets.count(), 1)

        response, data = self.post(self.url_2, {'property_values' : {}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReferenceSet.objects.count(), 2)
        self.assertEqual(self.project_2.reference_sets.count(), 1)

    def test_create_non_empty(self):
        response, data = self.post(self.url_1, {'property_values' : {"Property 1" : "Value 1"}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReferenceSet.objects.count(), 1)
        self.assertEqual(self.project_1.reference_sets.count(), 1)

        response, data = self.post(self.url_2, {'property_values' : {"Property 1" : "Value 1"}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReferenceSet.objects.count(), 2)
        self.assertEqual(self.project_2.reference_sets.count(), 1)

    def test_create_non_unique(self):
        response, data = self.post(self.url_1, {'property_values' : {"Property 1" : "Value 1", "Property 2" : "Value 2"}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReferenceSet.objects.count(), 1)
        self.assertEqual(self.project_1.reference_sets.count(), 1)

        with transaction.atomic():
            response, data = self.post(self.url_1, {'property_values' : {"Property 1" : "Value 1", "Property 2" : "Value 2"}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ReferenceSet.objects.count(), 1)
        self.assertEqual(self.project_1.reference_sets.count(), 1)

        with transaction.atomic():
            response, data = self.post(self.url_1, {'property_values' : {"Property 2" : "Value 2", "Property 1" : "Value 1"}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(ReferenceSet.objects.count(), 1)
        self.assertEqual(self.project_1.reference_sets.count(), 1)

    def test_create_force_create_date(self):
        created = datetime.datetime(year=2020, month=11, day=17, hour=14, minute=44, tzinfo=datetime.timezone(+datetime.timedelta(hours=1)))
        payload = {
            'created': created.isoformat(),
            'property_values' : {}
        }
        response, data = self.post(self.url_1, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.project_1.reference_sets.count(), 1)
        reference_set = self.project_1.reference_sets.first()
        self.assertEqual(reference_set.created, created)

    def test_get(self):
        self.post(self.url_1, {'property_values' : {}})
        self.post(self.url_1, {'property_values' : {"Property 1" : "Value 1"}})
        self.post(self.url_2, {'property_values' : {"Property 1" : "Value 1"}})
        response = client.get(self.url_1)
        reference_sets = self.project_1.reference_sets.order_by('-pk')
        serializer = ReferenceSetSerializer(reference_sets, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get(self.url_2)
        reference_sets = self.project_2.reference_sets.order_by('-pk')
        serializer = ReferenceSetSerializer(reference_sets, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_query(self):
        _, data = self.post(self.url_2, {'property_values' : {"Property 1" : "Value 1", "Property 2" : "Value 1", "Property 3" : "Value 1"}})
        reference_set_1 = self.project_2.reference_sets.get(id=data['id'])
        serializer_1 = ReferenceSetSerializer(reference_set_1)
        _, data = self.post(self.url_2, {'property_values' : {"Property 1" : "Value 1", "Property 2" : "Value 2", "Property 3" : "Value 2"}})
        reference_set_2 = self.project_2.reference_sets.get(id=data['id'])
        serializer_2 = ReferenceSetSerializer(reference_set_2)
        _, data = self.post(self.url_2, {'property_values' : {"Property 1" : "Value 2", "Property 2" : "Value 2", "Property 3" : "Value 3"}})
        reference_set_3 = self.project_2.reference_sets.get(id=data['id'])
        serializer_3 = ReferenceSetSerializer(reference_set_3)

        # Filter for 'Property 1' only:
        # we should get two results
        response = client.get(self.url_2, {"Property 1" : "Value 1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0], serializer_2.data)
        self.assertEqual(response.data[1], serializer_1.data)

        # Filter for 'Property 1' and 'Property 2':
        # we should get a single result
        response = client.get(self.url_2, {"Property 1" : "Value 1", "Property 2" : "Value 2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0], serializer_2.data)

        # Filter for 'Property 1' and 'Property 2':
        # we should get no results
        response = client.get(self.url_2, {"Property 1" : "Value 1", "Property 2" : "Value 3"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Filter for 'Property 1' and 'Property 3':
        # Since Property 3 does not influence the reference, we still get two results
        response = client.get(self.url_2, {"Property 1" : "Value 1", "Property 3" : "Value 2"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0], serializer_2.data)
        self.assertEqual(response.data[1], serializer_1.data)

class ReferenceSetApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        create_url = reverse('api_project_references', kwargs={'project_id' : self.project_id})

        response, data = self.post(create_url, {'property_values' : {}})
        self.reference_set_1_id = data['id']
        self.url_1 = reverse('api_project_reference', kwargs={'project_id' : self.project_id, 'reference_id' : self.reference_set_1_id})
        self.reference_set_1 = ReferenceSet.objects.get(id=self.reference_set_1_id)

        response, data = self.post(create_url, {'property_values' : {"Property 1" : "Value 1", "Property 2" : "Value 1"}})
        self.reference_set_2_id = data['id']
        self.url_2 = reverse('api_project_reference', kwargs={'project_id' : self.project_id, 'reference_id' : self.reference_set_2_id})
        self.reference_set_2 = ReferenceSet.objects.get(id=self.reference_set_2_id)

        response, data = self.post(create_url, {'property_values' : {"Property 1" : "Value 2", "Property 2" : "Value 1"}})
        self.reference_set_3_id = data['id']
        self.url_3 = reverse('api_project_reference', kwargs={'project_id' : self.project_id, 'reference_id' : self.reference_set_3_id})
        self.reference_set_3 = ReferenceSet.objects.get(id=self.reference_set_3_id)

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ReferenceSetSerializer(self.reference_set_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ReferenceSetSerializer(self.reference_set_2)
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_3)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ReferenceSetSerializer(self.reference_set_3)
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_reference', kwargs={'project_id' : "invalid", 'reference_id' : self.reference_set_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_reference', kwargs={'project_id' : self.project_id, 'reference_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response.data['property_values']['Property 1'] = "Value 3"
        response, data = self.put(self.url_1, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        reference_set = ReferenceSet.objects.get(id=self.reference_set_1_id)
        self.assertEqual(reference_set.property_values, {"Property 1" : "Value 3"})

    def test_modify_non_unique(self):
        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Try to modify reference set 2 to have the same property values as reference set 3
        response.data['property_values'] = self.reference_set_3.property_values
        response, data = self.put(self.url_2, response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ReferenceSet.objects.count(), 2)

class TestReferencesApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project 1", "test-project-1")
        self.project_id = data['id']
        self.project = Project.objects.get(id=data['id'])
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id = data['id']

        create_test_url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id})
        _, data = self.post(create_test_url, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}]})
        self.test_1_1_id = data['id']
        self.test_1_1 = TestResult.objects.get(id=self.test_1_1_id)
        _, data = self.post(create_test_url, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 2, 'type' : 'integer'}}]})
        self.test_1_2_id = data['id']
        self.test_1_2 = TestResult.objects.get(id=self.test_1_2_id)
        _, data = self.post(create_test_url, {'name' : 'Test 2', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}, {'name' : 'Result2', 'value' : { 'data' : 1.0, 'type' : 'float'}}]})
        self.test_2_1_id = data['id']
        self.test_2_1 = TestResult.objects.get(id=self.test_2_1_id)
        _, data = self.post(create_test_url, {'name' : 'Test 2', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 2, 'type' : 'integer'}}, {'name' : 'Result2', 'value' : { 'data' : 2.0, 'type' : 'float'}}]})
        self.test_2_2_id = data['id']
        self.test_2_2 = TestResult.objects.get(id=self.test_2_2_id)

        create_reference_set_url = reverse('api_project_references', kwargs={'project_id' : self.project_id})
        _, data = self.post(create_reference_set_url, {'property_values' : {}})
        self.reference_set_1_id = data['id']
        self.reference_set_1 = ReferenceSet.objects.get(id=self.reference_set_1_id)

        self.url = reverse('api_project_reference_tests', kwargs={'project_id' : self.project_id, 'reference_id' : self.reference_set_1_id})

    def test_create_empty(self):
        response, data = self.post(self.url, {'test_name' : 'Test 1', 'default_source' : self.test_1_1_id, 'references' : {}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestReference.objects.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)

    def test_create_non_empty(self):
        response, data = self.post(self.url, {'test_name' : "Test 1", 'default_source' : self.test_1_1_id, 'references' : {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}}}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestReference.objects.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.first().references, {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_1_1_id}})

    def test_create_explicit_test_id(self):
        response, data = self.post(self.url, {'test_name' : "Test 2", 'default_source' : self.test_2_1_id, 'references' : {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_2_2_id}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'}, 'source' : self.test_2_1_id}}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestReference.objects.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.first().references, {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_2_2_id}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'}, 'source' : self.test_2_1_id}})

    def test_create_only_explicit_test_id(self):
        response, data = self.post(self.url, {'test_name' : "Test 2", 'references' : {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_2_2_id}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'}, 'source' : self.test_2_1_id}}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestReference.objects.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.first().references, {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_2_2_id}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'}, 'source' : self.test_2_1_id}})

    def test_create_default_and_explicit_test_id(self):
        response, data = self.post(self.url, {'test_name' : "Test 2", 'default_source' : self.test_2_1_id, 'references' : {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_2_2_id}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'} }}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestReference.objects.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.first().references, {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_2_2_id}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'}, 'source' : self.test_2_1_id}})

    def test_create_null_value(self):
        response, data = self.post(self.url, {'test_name' : "Test 1", 'default_source' : self.test_1_1_id, 'references' : {'Result1' : {'value' : None}}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestReference.objects.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.first().references, {'Result1' : {'value' : None, 'source' : self.test_1_1_id}})

    def test_create_missing_test_id(self):
        response, data = self.post(self.url, {'test_name' : "Test 2", 'references' : {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_2_2_id}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'} }}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TestReference.objects.count(), 0)
        self.assertEqual(self.reference_set_1.test_references.count(), 0)

    def test_create_invalid(self):
        response, data = self.post(self.url, {'test_name' : "Test 2", 'references' : []})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TestReference.objects.count(), 0)
        self.assertEqual(self.reference_set_1.test_references.count(), 0)

        response, data = self.post(self.url, {'test_name' : "Test 2", 'references' : {'Result1' : {'source' : self.test_2_2_id}}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TestReference.objects.count(), 0)
        self.assertEqual(self.reference_set_1.test_references.count(), 0)

    def test_create_non_unique(self):
        response, data = self.post(self.url, {'test_name' : "Test 1", 'default_source' : self.test_1_1_id, 'references' : {}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TestReference.objects.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)

        with transaction.atomic():
            response, data = self.post(self.url, {'test_name' : "Test 1", 'default_source' : self.test_1_1_id, 'references' : {}})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(TestReference.objects.count(), 1)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)

    def test_create_force_create_date(self):
        created = datetime.datetime(year=2020, month=11, day=17, hour=14, minute=44, tzinfo=datetime.timezone(+datetime.timedelta(hours=1)))
        payload = {
            'test_name' : "Test 1",
            'default_source' : self.test_1_1_id,
            'references' : {},
            'created': created.isoformat()
        }
        response, data = self.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.reference_set_1.test_references.count(), 1)
        test_reference = self.reference_set_1.test_references.first()
        self.assertEqual(test_reference.created, created)

    def test_get(self):
        self.post(self.url, {'test_name' : "Test 1", 'default_source' : self.test_1_1_id, 'references' : {'Result1' : {'value' : 2}}})
        self.post(self.url, {'test_name' : "Test 2", 'default_source' : self.test_2_1_id, 'references' : {'Result1' : {'value' : 2}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'}}}})
        response = client.get(self.url)
        test_references = self.reference_set_1.test_references.order_by('-pk')
        serializer = TestReferenceSerializer(test_references, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_query(self):
        self.post(self.url, {'test_name' : "Test 1", 'default_source' : self.test_1_1_id, 'references' : {'Result1' : {'value' : 2}}})
        self.post(self.url, {'test_name' : "Test 2", 'default_source' : self.test_2_1_id, 'references' : {'Result1' : {'value' : 2}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'}}}})

        response = client.get(self.url, {"test_name" : "Test 1"})
        test_references = self.reference_set_1.test_references.filter(test_name='Test 1').order_by('-pk')
        serializer = TestReferenceSerializer(test_references, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get(self.url, {"test_name" : "Test 2"})
        test_references = self.reference_set_1.test_references.filter(test_name='Test 2').order_by('-pk')
        serializer = TestReferenceSerializer(test_references, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        response = client.get(self.url, {"test_name" : "DoesNotExit"})
        self.assertEqual(response.data, [])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class TestReferenceApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project 1", "test-project-1")
        self.project_id = data['id']
        self.project = Project.objects.get(id=data['id'])
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id = data['id']

        create_test_url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id})
        _, data = self.post(create_test_url, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}]})
        self.test_1_id = data['id']
        self.test_1 = TestResult.objects.get(id=self.test_1_id)
        _, data = self.post(create_test_url, {'name' : 'Test 2', 'results' : [{'name' : 'Result1', 'value' : { 'data' : 1, 'type' : 'integer'}}, {'name' : 'Result2', 'value' : { 'data' : 1.0, 'type' : 'float'}}]})
        self.test_2_id = data['id']
        self.test_2 = TestResult.objects.get(id=self.test_2_id)

        create_reference_set_url = reverse('api_project_references', kwargs={'project_id' : self.project_id})
        _, data = self.post(create_reference_set_url, {'property_values' : {}})
        self.reference_set_1_id = data['id']
        self.reference_set_1 = ReferenceSet.objects.get(id=self.reference_set_1_id)

        create_test_reference_url = reverse('api_project_reference_tests', kwargs={'project_id' : self.project_id, 'reference_id' : self.reference_set_1_id})
        _, data = self.post(create_test_reference_url, {'test_name' : "Test 1", 'default_source' : self.test_1_id, 'references' : {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}}}})
        self.test_reference_1_id = data['id']
        self.test_reference_1 = TestReference.objects.get(id=self.test_reference_1_id)
        _, data = self.post(create_test_reference_url, {'test_name' : "Test 2", 'default_source' : self.test_2_id, 'references' : {'Result1' : {'value' : { 'data' : 2, 'type' : 'integer'}}, 'Result2' : {'value' : { 'data' : 3.0, 'type' : 'float'}}}})
        self.test_reference_2_id = data['id']
        self.test_reference_2 = TestReference.objects.get(id=self.test_reference_2_id)

        self.url_1 = reverse('api_project_reference_test', kwargs={'project_id' : self.project_id, 'reference_id' : self.reference_set_1_id, 'test_id' : self.test_reference_1_id})
        self.url_2 = reverse('api_project_reference_test', kwargs={'project_id' : self.project_id, 'reference_id' : self.reference_set_1_id, 'test_id' : self.test_reference_2_id})

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TestReferenceSerializer(self.test_reference_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TestReferenceSerializer(self.test_reference_2)
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_reference_test', kwargs={'project_id' : "invalid", 'reference_id' : self.reference_set_1_id, 'test_id' : self.test_reference_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_reference_test', kwargs={'project_id' : self.project_id, 'reference_id' : 123, 'test_id' : self.test_reference_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        response = client.get(reverse('api_project_reference_test', kwargs={'project_id' : self.project_id, 'reference_id' : self.reference_set_1_id, 'test_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = copy.deepcopy(response.data)
        data['default_source'] = self.test_1_id
        data['references']['Result2'] = {'value' : { 'data' : 3, 'type' : 'integer'}}
        response, data = self.put(self.url_1, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_reference_1 = TestReference.objects.get(id=self.test_reference_1_id)
        self.assertEqual(test_reference_1.references["Result2"], {'value' : { 'data' : 3, 'type' : 'integer'}, 'source' : self.test_1_id})

    def test_update_new(self):
        data = {}
        data['default_source'] = self.test_1_id
        data['references'] = {'Result2' : {'value' : { 'data' : 3, 'type' : 'integer'}}}
        response, data = self.patch(self.url_1, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_reference_1 = TestReference.objects.get(id=self.test_reference_1_id)
        self.assertEqual(test_reference_1.references["Result1"], {'value' : { 'data' : 2, 'type' : 'integer'}, 'source' : self.test_1_id})
        self.assertEqual(test_reference_1.references["Result2"], {'value' : { 'data' : 3, 'type' : 'integer'}, 'source' : self.test_1_id})

    def test_update_change(self):
        data = {}
        data['default_source'] = self.test_1_id
        data['references'] = {'Result1' : {'value' : { 'data' : 3, 'type' : 'integer'}}}
        response, data = self.patch(self.url_1, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_reference_1 = TestReference.objects.get(id=self.test_reference_1_id)
        self.assertEqual(test_reference_1.references["Result1"], {'value' : { 'data' : 3, 'type' : 'integer'}, 'source' : self.test_1_id})

    def test_update_change_to_null(self):
        data = {}
        data['default_source'] = self.test_1_id
        data['references'] = {'Result1' : {'value' : None}}
        response, data = self.patch(self.url_1, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_reference_1 = TestReference.objects.get(id=self.test_reference_1_id)
        self.assertEqual(test_reference_1.references["Result1"], {'value' : None, 'source' : self.test_1_id})

    def test_update_remove(self):
        data = {}
        data['default_source'] = self.test_2_id
        data['references'] = {'Result1' : None}
        response, data = self.patch(self.url_2, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_reference_2 = TestReference.objects.get(id=self.test_reference_2_id)
        self.assertFalse("Result1" in test_reference_2.references)
        self.assertEqual(test_reference_2.references["Result2"], {'value' : { 'data' : 3.0, 'type' : 'float'}, 'source' : self.test_2_id})

    def test_delete(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TestReference.objects.count(), 1)

class WebhooksApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project 1", "test-project-1")
        self.project_1_id = data['id']
        self.project_1 = Project.objects.get(id=self.project_1_id)
        self.url_1 = reverse('api_project_webhooks', kwargs={'project_id' : self.project_1_id})

        _, data = self.create_project("Test Project 2", "test-project-2")
        self.project_2_id = data['id']
        self.project_2 = Project.objects.get(id=self.project_2_id)
        self.url_2 = reverse('api_project_webhooks', kwargs={'project_id' : self.project_2_id})

    def test_create(self):
        response, data = self.post(self.url_1, {'name' : "Hook 1", 'url' : 'http://example.com/webhook', 'secret_token' : 'token' })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Webhook.objects.count(), 1)
        self.assertEqual(self.project_1.webhooks.count(), 1)

        response, data = self.post(self.url_2, {'name' : "Hook 2", 'url' : 'http://example.com/webhook', 'secret_token' : 'token' })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Webhook.objects.count(), 2)
        self.assertEqual(self.project_2.webhooks.count(), 1)

    def test_create_invalid(self):
        response, data = self.post(self.url_1, {'name' : "Hook 1", 'url' : 'Not A Valid URL', 'secret_token' : 'token' })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Webhook.objects.count(), 0)
        self.assertEqual(self.project_1.webhooks.count(), 0)

    def test_get(self):
        self.post(self.url_1, {'name' : "Hook 1", 'url' : 'http://example.com/webhook/1', 'secret_token' : 'token' })
        self.post(self.url_1, {'name' : "Hook 2", 'url' : 'http://example.com/webhook/2', 'secret_token' : 'token' })
        self.post(self.url_2, {'name' : "Hook 1", 'url' : 'http://example.com/webhook/3', 'secret_token' : 'token' })
        response = client.get(self.url_1)
        webhooks = self.project_1.webhooks.order_by('-pk')
        serializer = WebhookSerializer(webhooks, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = client.get(self.url_2)
        webhooks = self.project_2.webhooks.order_by('-pk')
        serializer = WebhookSerializer(webhooks, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class WebhookApiTest(ApiTestCase):
    def setUp(self):
        super().setUp()
        _, data = self.create_project("Test Project 1", "test-project-1")
        self.project_id = data['id']
        create_url = reverse('api_project_webhooks', kwargs={'project_id' : self.project_id})

        response, data = self.post(create_url, {'name' : "Hook 1", 'url' : 'http://example.com/webhook/1', 'secret_token' : 'token1' })
        self.webhook_1_id = data['id']
        self.url_1 = reverse('api_project_webhook', kwargs={'project_id' : self.project_id, 'webhook_id' : self.webhook_1_id})
        self.webhook_1 = Webhook.objects.get(id=self.webhook_1_id)

        response, data = self.post(create_url, {'name' : "Hook 2", 'url' : 'http://example.com/webhook/2', 'secret_token' : 'token2' })
        self.webhook_2_id = data['id']
        self.url_2 = reverse('api_project_webhook', kwargs={'project_id' : self.project_id, 'webhook_id' : self.webhook_2_id})
        self.webhook_2 = Webhook.objects.get(id=self.webhook_2_id)

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = WebhookSerializer(self.webhook_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = WebhookSerializer(self.webhook_2)
        self.assertEqual(response.data, serializer.data)

    def test_get_invalid(self):
        response = client.get(reverse('api_project_webhook', kwargs={'project_id' : "invalid", 'webhook_id' : self.webhook_1_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        response = client.get(reverse('api_project_webhook', kwargs={'project_id' : self.project_id, 'webhook_id' : 123}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_modify(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        new_name = "New Hook"
        response.data['name'] = new_name
        response, data = self.put(self.url_1, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        webhook = Webhook.objects.get(id=self.webhook_1_id)
        self.assertEqual(webhook.name, new_name)

    def test_modify_invalid_url(self):
        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response.data['url'] = "Not a valid URL"
        response, data = self.put(self.url_2, response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Webhook.objects.count(), 1)
