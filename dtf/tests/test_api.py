"""
Module containing the API unit tests

Tests:
create project
get_projects
submit_test_results
update_references
"""

import json

from rest_framework import status

from django.test import TestCase, Client
from django.urls import reverse
from django.utils.text import slugify

from dtf.models import Project, TestResult, TestReference, Submission
from dtf.serializers import ProjectSerializer
from dtf.serializers import TestResultSerializer

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
        response = client.post(
            '/api/create_project',
            json.dumps(valid_payload),
            content_type='application/json'
        )
        return response, response.data

    def create_submission(self, project_name):
        valid_payload = {
            'project_name':project_name
        }
        response = client.post(
            '/api/create_submission',
            json.dumps(valid_payload),
            content_type='application/json'
        )
        return response, response.data

# Create your tests here.
class ProjectApiTest(ApiTestCase):
    """ Test module for Project model interaction with API """
    def setUp(self):
        self.invalid_payload = {
            'not_a_name':'no name given'
        }

    def test_create_project_success(self):
        # Test success
        response, data = self.create_project("test", "test")
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['project_id'], 1)

        # Test invalid payload
        response, data = self.post(
            '/api/create_project',
            self.invalid_payload
        )
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(response.status_code, 400)

        # Test same name different slug
        response, data = self.create_project("test", "test-2")
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(response.status_code, 200)

        # Test invalid slug
        response, data = self.create_project("test", "invalid slug")
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(response.status_code, 400)

    def test_get_project_from_api(self):
        _ = self.create_project('test')
        response = client.get(reverse('get_projects'))
        projects = Project.objects.all()
        serializer = ProjectSerializer(projects, many=True)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class SubmissionApiTest(ApiTestCase):
    """ Test module for submissions"""

    def setUp(self):
        self.project_name = "submission_project"
        self.create_project(self.project_name)
        self.invalid_project_name = "does_not_exist"

    def test_create_submission(self):
        response, data = self.create_submission(self.project_name)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(data['id'], 1)
        response, _ = self.create_submission(self.invalid_project_name)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Submission.objects.count(), 1)

class TestResultApiTest(ApiTestCase):
    """ Test module for submitting test results via the API """

    def setUp(self):
        self.project_name = 'test_project'
        # create a test project to put test results in
        self.create_project(self.project_name)
        _, data = self.create_submission(self.project_name)
        self.submission_id = data['id']
        self.valid_payload = {
            "name":"UNIT_TEST",
            "results":[
                {
                    "name":"parameter1",
                    "value":5,
                    "valuetype":"integer"
                }
            ],
            "submission_id":1
        }
        self.missing_name_payload = {
            "results":[
            ],
            "submission":1
        }
        self.missing_submission_id_payload = {
            "name":"UNIT_TEST",
            "results":[
                {
                    "name":"parameter1",
                    "value":5,
                    "valuetype":"integer"
                }
            ]
        }

    def test_submit_test_results(self):
        # submit some test results to the api
        response, _ = self.post(
            '/api/submit_test_results',
            self.valid_payload,
        )
        self.assertEqual(TestResult.objects.count(), 1)
        self.assertEqual(response.status_code, 200)

        response, _ = self.post(
            '/api/submit_test_results',
            self.missing_name_payload
        )
        self.assertEqual(TestResult.objects.count(), 1)
        self.assertEqual(response.status_code, 400)

        response, _ = self.post(
            '/api/submit_test_results',
            self.missing_submission_id_payload
        )
        self.assertEqual(TestResult.objects.count(), 1)
        self.assertEqual(response.status_code, 400)

class TestReferenceApiTest(ApiTestCase):
    def setUp(self):
        self.test_name = "UNIT_TEST"
        self.project_name = 'test_project'
        # create a test project to put test results in
        self.create_project(self.project_name)
        _, data = self.create_submission(self.project_name)
        self.submission_id = data['id']
        # submit test results to update references for
        # on an empty/test database, the test_id will always be 1
        self.post(
        '/api/submit_test_results',
            {
                "name":self.test_name,
                "results":[
                    {
                        "name":"parameter1",
                        "value":5,
                        "valuetype":"integer"
                    }
                ],
                "submission_id":self.submission_id
            },
        )

        self.valid_payload = {
            "project_name":self.project_name,
            "test_name":self.test_name,
            "references":{
                "parameter1":
                {
                    "value":7
                }
            },
            "test_id": 1
        }

        self.new_references = {
            "project_name":self.project_name,
            "test_name":self.test_name,
            "references":{
                "parameter1":
                {
                    "value":23
                }
            },
            "test_id": 1
        }
        self.missing_id = {
            "project_name":self.project_name,
            "test_name":self.test_name,
            "references":{
                "parameter1":
                {
                    "value":23
                }
            }
        }
        self.invalid_id = {
            "project_name":self.project_name,
            "test_name":self.test_name,
            "references":{
                "parameter1":
                {
                    "value":23
                }
            },
            "test_id": 999999
        }


    def test_update_test_references(self):
        response, _ = self.put(
            '/api/update_references',
            self.valid_payload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        references = TestReference.objects.all()
        self.assertEqual(len(references), 1)

        response, _ = self.put(
            '/api/update_references',
            self.new_references
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        references = TestReference.objects.all()
        self.assertEqual(len(references), 1)

        response, _ = self.put(
            '/api/update_references',
            self.missing_id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response, _ = self.put(
            '/api/update_references',
            self.invalid_id
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = client.get(reverse('get_reference', kwargs={
            "project_name":self.project_name,
            "test_name": self.test_name
        }))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['test_name'], self.test_name)
        
        response_alternative = client.get(reverse('get_reference_by_test_id', kwargs={
            "test_id":1
        }))
        self.assertEqual(response_alternative.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['test_name'], self.test_name)
        self.assertEqual(response.data, response_alternative.data)
