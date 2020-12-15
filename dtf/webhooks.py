
import concurrent

import requests

from django.db.models import signals

from dtf.models import Submission, TestResult, ReferenceSet, TestReference
from dtf.serializers import SubmissionSerializer, TestResultSerializer, ReferenceSetSerializer, TestReferenceSerializer

class WebhookExecutionPool(concurrent.futures.ThreadPoolExecutor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._outstanding_futures = []

    def submit(self, *args, **kwargs):
        future = super().submit(*args, **kwargs)

        self._outstanding_futures.append(future)
        future.add_done_callback(lambda f: self._outstanding_futures.remove(f))

        return future

    def wait(self, timeout=None):
        current_outstanging = list(self._outstanding_futures)
        concurrent.futures.wait(current_outstanging, timeout=timeout)

webhook_execution_pool = WebhookExecutionPool(max_workers=4)


def _submit_webhook_request(request):
    prepared_request = request.prepare()

    with requests.Session() as session:
        try:
            response = session.send(prepared_request)
        except requests.RequestException as e:
            pass
        else:
            pass

def trigger_webhook(webhook, data):
    headers = {
        "X-DTF-Token": webhook.secret_token,
        "Content-Type": "application/json"
    }

    request = requests.Request('POST', webhook.url, data=data, headers=headers)

    webhook_execution_pool.submit(_submit_webhook_request, request)

def _get_webhooks(instance):
    if isinstance(instance, Submission):
        return instance.project.webhooks.filter(on_submission=True)
    elif isinstance(instance, TestResult):
        return instance.submission.project.webhooks.filter(on_test_result=True)
    elif isinstance(instance, ReferenceSet):
        return instance.project.webhooks.filter(on_reference_set=True)
    elif isinstance(instance, TestReference):
        return instance.reference_set.project.webhooks.filter(on_test_reference=True)

def _serialize(instance):
    if isinstance(instance, Submission):
        return SubmissionSerializer(instance).data
    elif isinstance(instance, TestResult):
        return TestResultSerializer(instance).data
    elif isinstance(instance, ReferenceSet):
        return ReferenceSetSerializer(instance).data
    elif isinstance(instance, TestReference):
        return TestReferenceSerializer(instance).data

def trigger_webhooks(event, instance):
    data = {
        'event' : event,
        'data' : _serialize(instance)
    }
    for webhook in _get_webhooks(instance):
        trigger_webhook(webhook, data)

def _on_model_save(sender, instance, created, **kwargs):
    trigger_webhooks('create' if created else 'edit', instance)

def _on_model_delete(sender, instance, **kwargs):
    trigger_webhooks('delete', instance)

def connect_webhook_signals():
    webhook_models = [Submission, TestResult, ReferenceSet, TestReference]

    for model in webhook_models:
        lower_name = model.__name__.lower()
        signals.post_save.connect(_on_model_save, sender=model, dispatch_uid=f"webhook_{lower_name}_save")
        signals.post_delete.connect(_on_model_delete, sender=model, dispatch_uid=f"webhook_{lower_name}_delete")
