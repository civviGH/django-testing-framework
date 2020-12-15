
from unittest.mock import patch

from django.test import TestCase

from dtf.models import Project, TestResult, ReferenceSet, TestReference, Submission, Webhook
from dtf.serializers import SubmissionSerializer, TestResultSerializer, ReferenceSetSerializer, TestReferenceSerializer

class WebhooksTest(TestCase):
    def setUp(self):
        self.project = Project(name="Test Project", slug="test-project")
        self.project.save()

        self.all_webhook = Webhook(project=self.project, name="All", url="http://example.com/webhook/all", secret_token="all_token",
            on_submission=True,
            on_test_result=True,
            on_reference_set=True,
            on_test_reference=True
        )
        self.all_webhook.save()

        self.submission_webhook = Webhook(project=self.project, name="Submission", url="http://example.com/webhook/submission", secret_token="submission_token",
            on_submission=True,
            on_test_result=False,
            on_reference_set=False,
            on_test_reference=False
        )
        self.submission_webhook.save()

        self.test_result_webhook = Webhook(project=self.project, name="Test Result", url="http://example.com/webhook/test_result", secret_token="test_result_token",
            on_submission=False,
            on_test_result=True,
            on_reference_set=False,
            on_test_reference=False
        )
        self.test_result_webhook.save()

        self.reference_set_webhook = Webhook(project=self.project, name="Reference Set", url="http://example.com/webhook/reference_set", secret_token="reference_set_token",
            on_submission=False,
            on_test_result=False,
            on_reference_set=True,
            on_test_reference=False
        )
        self.reference_set_webhook.save()

        self.test_reference_webhook = Webhook(project=self.project, name="Test Reference", url="http://example.com/webhook/test_reference", secret_token="test_reference_token",
            on_submission=False,
            on_test_result=False,
            on_reference_set=False,
            on_test_reference=True
        )
        self.test_reference_webhook.save()

    def _check_webhook_submission(self, call_args, event_type, data, required_webhooks):
        (request,) = call_args.args

        self.assertEqual(request.method, "POST")
        self.assertEqual(request.data['event'], event_type)
        self.assertEqual(request.data['data'], data)

        found_webhook = False
        for index in range(len(required_webhooks)):
            webhook = required_webhooks[index]
            if webhook.url == request.url:
                self.assertEqual(request.headers['X-DTF-Token'], webhook.secret_token)

                del required_webhooks[index]
                found_webhook = True
                break

        self.assertTrue(found_webhook)

    def test_on_submission(self):
        submission = Submission(project=self.project)

        # Create
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            submission.save()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.submission_webhook]

            data = SubmissionSerializer(submission).data
            self._check_webhook_submission(submit_mock.call_args_list[0], 'create', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'create', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

        # Edit
        submission.info = {'Key' : 'Value'}
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            submission.save()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.submission_webhook]

            data = SubmissionSerializer(submission).data
            self._check_webhook_submission(submit_mock.call_args_list[0], 'edit', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'edit', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

        # Delete
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            excepted_data = SubmissionSerializer(submission).data
            submission.delete()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.submission_webhook]

            self._check_webhook_submission(submit_mock.call_args_list[0], 'delete', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'delete', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

    def test_on_test_result(self):
        submission = Submission(project=self.project)
        with patch('dtf.webhooks._submit_webhook_request'):
            submission.save()
        test_result = TestResult(submission=submission, name="Test 1", results=[{'name' : 'Result1', 'value' : 1, 'valuetype' : 'integer', 'status' : 'successful'}])

        # Create
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            test_result.save()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.test_result_webhook]

            data = TestResultSerializer(test_result).data
            self._check_webhook_submission(submit_mock.call_args_list[0], 'create', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'create', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

        # Edit
        submission.results = [{'name' : 'Result1', 'value' : 2, 'valuetype' : 'integer', 'status' : 'failed'}]
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            test_result.save()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.test_result_webhook]

            data = TestResultSerializer(test_result).data
            self._check_webhook_submission(submit_mock.call_args_list[0], 'edit', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'edit', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

        # Delete
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            data = TestResultSerializer(test_result).data
            test_result.delete()
            self.assertEqual(submit_mock.call_count, 2)
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.test_result_webhook]

            self._check_webhook_submission(submit_mock.call_args_list[0], 'delete', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'delete', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

    def test_on_reference_set(self):
        submission = Submission(project=self.project)
        with patch('dtf.webhooks._submit_webhook_request'):
            submission.save()

        reference_set = ReferenceSet(project=self.project, property_values={"Key" : "Value"})

        # Create
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            reference_set.save()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.reference_set_webhook]

            data = ReferenceSetSerializer(reference_set).data
            self._check_webhook_submission(submit_mock.call_args_list[0], 'create', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'create', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

        # Edit
        reference_set.property_values = {"Key" : "Value2"}
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            reference_set.save()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.reference_set_webhook]

            data = ReferenceSetSerializer(reference_set).data
            self._check_webhook_submission(submit_mock.call_args_list[0], 'edit', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'edit', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

        # Delete
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            data = ReferenceSetSerializer(reference_set).data
            reference_set.delete()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.reference_set_webhook]

            self._check_webhook_submission(submit_mock.call_args_list[0], 'delete', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'delete', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

    def test_on_test_reference(self):
        submission = Submission(project=self.project)
        with patch('dtf.webhooks._submit_webhook_request'):
            submission.save()

        test_result = TestResult(submission=submission, name="Test 1", results=[{'name' : 'Result1', 'value' : 1, 'valuetype' : 'integer', 'status' : 'successful'}])
        with patch('dtf.webhooks._submit_webhook_request'):
            test_result.save()

        reference_set = ReferenceSet(project=self.project, property_values={"Key" : "Value"})
        with patch('dtf.webhooks._submit_webhook_request'):
            reference_set.save()

        test_reference = TestReference(reference_set=reference_set, test_name="Test 1", references={'Result1' : {'value' : 2, 'ref_id' : test_result.id}})

        # Create
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            test_reference.save()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.test_reference_webhook]

            data = TestReferenceSerializer(test_reference).data
            self._check_webhook_submission(submit_mock.call_args_list[0], 'create', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'create', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

        # Edit
        test_reference.references={'Result1' : {'value' : 1, 'ref_id' : test_result.id}}
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            test_reference.save()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.test_reference_webhook]

            data = TestReferenceSerializer(test_reference).data
            self._check_webhook_submission(submit_mock.call_args_list[0], 'edit', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'edit', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)

        # Delete
        with patch('dtf.webhooks._submit_webhook_request') as submit_mock:
            data = TestReferenceSerializer(test_reference).data
            test_reference.delete()
            self.assertEqual(submit_mock.call_count, 2)

            required_webhooks = [self.all_webhook, self.test_reference_webhook]

            self._check_webhook_submission(submit_mock.call_args_list[0], 'delete', data, required_webhooks)
            self._check_webhook_submission(submit_mock.call_args_list[1], 'delete', data, required_webhooks)

            self.assertEqual(len(required_webhooks), 0)
