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

from rest_framework import status

from django.test import TestCase, Client
from django.urls import reverse
from django.utils.text import slugify
from django.db import transaction

from dtf.models import Project, TestResult, ReferenceSet, TestReference, Submission, ProjectSubmissionProperty
from dtf.serializers import ProjectSerializer
from dtf.serializers import TestResultSerializer
from dtf.serializers import ProjectSubmissionPropertySerializer
from dtf.serializers import SubmissionSerializer
from dtf.serializers import ReferenceSetSerializer

client = Client()

class ApiTestCase(TestCase):

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

    def create_project(self, name, slug=None):
        if slug is None:
            slug = slugify(name)
        valid_payload = {
            'name':name,
            'slug':slug
        }
        return self.post(reverse('api_projects'), valid_payload)

    def create_submission(self, project_id=None, info=None):
        valid_payload = {}
        if info is not None:
            valid_payload['info'] = info

        return self.post(reverse('api_project_submissions', kwargs={'project_id' : project_id}), valid_payload)

# Create your tests here.
class ProjectsApiTest(ApiTestCase):
    """ Test module for Project model interaction with API """
    def setUp(self):
        self.invalid_payload = {
            'not_a_name':'no name given'
        }

    def test_create_project(self):
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

        # Test same name, different slug
        response, data = self.create_project("Test Project", "other-slug")
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Test invalid slug
        response, data = self.create_project("Test Project", "Invalid Slug")
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_projects(self):
        _ = self.create_project('Test Project 1')
        _ = self.create_project('Test Project 2')
        _ = self.create_project('Test/Project#?3')
        response = client.get(reverse('api_projects'))
        projects = Project.objects.order_by('-pk')
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class ProjectApiTest(ApiTestCase):
    def setUp(self):
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
        serializer = ProjectSerializer(self.project_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(reverse('api_project', kwargs={'id' : self.project_2_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSerializer(self.project_2)
        self.assertEqual(response.data, serializer.data)

    def test_get_project_slug(self):
        response = client.get(reverse('api_project', kwargs={'id' : self.project_1_slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSerializer(self.project_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(reverse('api_project', kwargs={'id' : self.project_2_slug}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = ProjectSerializer(self.project_2)
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

class ProjectSubmissionPropertiesApiTest(ApiTestCase):
    def setUp(self):
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
        self.project_name = "Submission Project"
        self.project_slug = "submission-project"
        _, data = self.create_project(self.project_name, self.project_slug)
        self.project_id = data['id']

        self.invalid_project_slug = "does-not-exist"
        self.invalid_project_id = "123"

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

    def test_get(self):
        self.create_submission(project_id=self.project_id, info={"Key": "Value"})
        self.create_submission(project_id=self.project_id, info={"Key": "Value"})
        response = client.get(reverse('api_project_submissions', kwargs={'project_id' : self.project_id}))
        submissions = Submission.objects.order_by('-pk')
        serializer = SubmissionSerializer(submissions, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class SubmissionApiTest(ApiTestCase):
    def setUp(self):
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
        serializer = SubmissionSerializer(self.submission_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = SubmissionSerializer(self.submission_2)
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
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id = data['id']

        self.url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id})

        self.valid_payload = {
            "name":"UNIT_TEST",
            "results":[
                {
                    "name":"parameter1",
                    "value":5,
                    "valuetype":"integer"
                }
            ],
        }

        self.missing_name_payload = {
            "results":[
            ]
        }

    def test_create(self):
        response, data = self.post(self.url, self.valid_payload)
        self.assertEqual(TestResult.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['name'], self.valid_payload['name'])
        self.assertEqual(data['results'][0]["name"], self.valid_payload['results'][0]["name"])
        self.assertEqual(data['results'][0]["value"], self.valid_payload['results'][0]["value"])
        self.assertEqual(data['results'][0]["valuetype"], self.valid_payload['results'][0]["valuetype"])

    def test_create_invalid(self):
        response, data = self.post(self.url, self.missing_name_payload)
        self.assertEqual(TestResult.objects.count(), 0)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get(self):
        response, data = self.post(self.url, self.valid_payload)
        response = client.get(self.url)
        tests = TestResult.objects.order_by('-pk')
        serializer = TestResultSerializer(tests, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class TestResultApiTest(ApiTestCase):
    def setUp(self):
        _, data = self.create_project("Test Project", "test-project")
        self.project_id = data['id']
        _, data = self.create_submission(project_id=self.project_id)
        self.submission_id = data['id']
        create_url = reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id})

        response, data = self.post(create_url, {'name' : 'Test 1', 'results' : [{'name' : 'Result1', 'value' : 1, 'valuetype' : 'integer'}]})
        self.test_1_id = data['id']
        self.url_1 = reverse('api_project_submission_test', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id, 'test_id' : self.test_1_id})
        self.test_1 = TestResult.objects.get(id=self.test_1_id)

        response, data = self.post(create_url, {'name' : 'Test 2', 'results' : [{'name' : 'Result1', 'value' : 1, 'valuetype' : 'integer'}]})
        self.test_2_id = data['id']
        self.url_2 = reverse('api_project_submission_test', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id, 'test_id' : self.test_2_id})
        self.test_2 = TestResult.objects.get(id=self.test_2_id)

    def test_get(self):
        response = client.get(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TestResultSerializer(self.test_1)
        self.assertEqual(response.data, serializer.data)

        response = client.get(self.url_2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        serializer = TestResultSerializer(self.test_2)
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
        new_test_data = {'name' : 'Result2', 'value' : 2, 'valuetype' : 'integer'}
        response.data['results'].append(new_test_data)
        response, data = self.put(self.url_1, response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_1 = TestResult.objects.get(id=self.test_1_id)
        self.assertEqual(test_1.name, new_name)
        self.assertEqual(test_1.results[1]["name"], new_test_data["name"])
        self.assertEqual(test_1.results[1]["value"], new_test_data["value"])
        self.assertEqual(test_1.results[1]["valuetype"], new_test_data["valuetype"])

    def test_delete(self):
        response = client.delete(self.url_1)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 1)

class ReferenceSetsApiTest(ApiTestCase):
    def setUp(self):
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

class ReferenceSetApiTest(ApiTestCase):
    def setUp(self):
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

# class TestReferenceApiTest(ApiTestCase):
#     def setUp(self):
#         self.test_name = "UNIT_TEST"
#         self.project_name = "Test Project"
#         self.project_slug = "test-project"
#         # create a test project to put test results in
#         _, data = self.create_project(self.project_name, self.project_slug)
#         self.project_id = data['id']

#         _, data = self.create_submission(project_id=self.project_id)
#         self.submission_id = data['id']
#         # submit test results to update references for
#         # on an empty/test database, the test_id will always be 1
#         self.post(reverse('api_project_submission_tests', kwargs={'project_id' : self.project_id, 'submission_id' : self.submission_id}),
#             {
#                 "name":self.test_name,
#                 "results":[
#                     {
#                         "name":"parameter1",
#                         "value":5,
#                         "valuetype":"integer"
#                     }
#                 ]
#             },
#         )

#         self.valid_payload = {
#             "project_id":self.project_id,
#             "test_name":self.test_name,
#             "references":{
#                 "parameter1":
#                 {
#                     "value":7
#                 }
#             },
#             "test_id": 1
#         }

#         self.new_references = {
#             "project_id":self.project_id,
#             "test_name":self.test_name,
#             "references":{
#                 "parameter1":
#                 {
#                     "value":23
#                 }
#             },
#             "test_id": 1
#         }
#         self.missing_id = {
#             "project_id":self.project_id,
#             "test_name":self.test_name,
#             "references":{
#                 "parameter1":
#                 {
#                     "value":23
#                 }
#             }
#         }
#         self.invalid_id = {
#             "project_id":self.project_id,
#             "test_name":self.test_name,
#             "references":{
#                 "parameter1":
#                 {
#                     "value":23
#                 }
#             },
#             "test_id": 999999
#         }


#     def test_update_test_references(self):
#         response, _ = self.put(
#             '/api/update_references',
#             self.valid_payload
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         references = TestReference.objects.all()
#         self.assertEqual(len(references), 1)

#         response, _ = self.put(
#             '/api/update_references',
#             self.new_references
#         )
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         references = TestReference.objects.all()
#         self.assertEqual(len(references), 1)

#         response, _ = self.put(
#             '/api/update_references',
#             self.missing_id
#         )
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#         response, _ = self.put(
#             '/api/update_references',
#             self.invalid_id
#         )
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#         response = client.get(reverse('get_reference', kwargs={
#             "project_slug":self.project_slug,
#             "test_name": self.test_name
#         }))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['test_name'], self.test_name)
        
#         response_alternative = client.get(reverse('get_reference_by_test_id', kwargs={
#             "test_id":1
#         }))
#         self.assertEqual(response_alternative.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
#         self.assertEqual(response.data[0]['test_name'], self.test_name)
#         self.assertEqual(response.data, response_alternative.data)
