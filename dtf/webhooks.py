
import concurrent
import json

import requests

from django.conf import settings
from django.db.models import signals

from dtf.models import Submission, TestResult, ReferenceSet, TestReference, WebhookLogEntry
from dtf.serializers import ProjectSerializer, SubmissionSerializer, TestResultSerializer, ReferenceSetSerializer, TestReferenceSerializer

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

if settings.DTF_WEBHOOK_THREADPOOL:
    webhook_execution_pool = WebhookExecutionPool(max_workers=4)

def _submit_webhook_request(request, webhook_id, sender):
    prepared_request = request.prepare()

    with requests.Session() as session:
        try:
            response = session.send(prepared_request)
        except requests.RequestException as exception:
            webhook_log = WebhookLogEntry(webhook_id=webhook_id,
                                          trigger=sender.__name__,
                                          request_url=request.url,
                                          request_data=request.json,
                                          request_headers=dict(prepared_request.headers),
                                          response_status=0,
                                          response_data=str(exception),
                                          response_headers=dict())
        else:
            webhook_log = WebhookLogEntry(webhook_id=webhook_id,
                                          trigger=sender.__name__,
                                          request_url=request.url,
                                          request_data=request.json,
                                          request_headers=dict(prepared_request.headers),
                                          response_status=response.status_code,
                                          response_data=response.text,
                                          response_headers=dict(response.headers))

    webhook_log.save()

    # Delete old log entries
    max_logs_to_keep = 10
    log_ids = WebhookLogEntry.objects.filter(webhook_id=webhook_id).order_by('-created')[max_logs_to_keep:].values_list("id", flat=True)
    WebhookLogEntry.objects.filter(pk__in=log_ids).delete()

def trigger_webhook(webhook, data, sender):
    headers = {
        "X-DTF-Token": webhook.secret_token,
    }

    request = requests.Request('POST', webhook.url, json=data, headers=headers)

    if settings.DTF_WEBHOOK_THREADPOOL:
        webhook_execution_pool.submit(_submit_webhook_request, request, webhook.id, sender)
    else:
        _submit_webhook_request(request, webhook.id, sender)

def _get_webhooks(instance):
    if isinstance(instance, Submission):
        return instance.project.webhooks.filter(on_submission=True)
    elif isinstance(instance, TestResult):
        return instance.submission.project.webhooks.filter(on_test_result=True)
    elif isinstance(instance, ReferenceSet):
        return instance.project.webhooks.filter(on_reference_set=True)
    elif isinstance(instance, TestReference):
        return instance.reference_set.project.webhooks.filter(on_test_reference=True)

def _serialize_project(instance):
    if isinstance(instance, Submission):
        return ProjectSerializer(instance.project).data
    elif isinstance(instance, TestResult):
        return ProjectSerializer(instance.submission.project).data
    elif isinstance(instance, ReferenceSet):
        return ProjectSerializer(instance.project).data
    elif isinstance(instance, TestReference):
        return ProjectSerializer(instance.reference_set.project).data

def _serialize(instance):
    if isinstance(instance, Submission):
        return SubmissionSerializer(instance).data
    elif isinstance(instance, TestResult):
        return TestResultSerializer(instance).data
    elif isinstance(instance, ReferenceSet):
        return ReferenceSetSerializer(instance).data
    elif isinstance(instance, TestReference):
        return TestReferenceSerializer(instance).data

def trigger_webhooks(event, instance, sender):
    webhooks = _get_webhooks(instance)
    if webhooks.exists():
        data = {
            'event' : event,
            'source' : sender.__name__.lower(),
            'project' : _serialize_project(instance),
            'object' : _serialize(instance)
        }
        for webhook in webhooks:
            trigger_webhook(webhook, data, sender)

def _on_model_save(sender, instance, created, **kwargs):
    trigger_webhooks('create' if created else 'edit', instance, sender)

def _on_model_delete(sender, instance, **kwargs):
    # trigger_webhooks('delete', instance, sender)
    pass

def _on_pre_migrate(sender, **kwargs):
    disconnect_webhook_signals()

def _on_post_migrate(sender, **kwargs):
    connect_webhook_signals()

def disconnect_webhook_signals():
    webhook_models = [Submission, TestResult, ReferenceSet, TestReference]

    for model in webhook_models:
        lower_name = model.__name__.lower()
        signals.post_save.disconnect(sender=model, dispatch_uid=f"webhook_{lower_name}_save")
        signals.post_delete.disconnect(sender=model, dispatch_uid=f"webhook_{lower_name}_delete")

    signals.pre_migrate.disconnect(dispatch_uid=f"disable_webhooks_on_migration")
    signals.post_migrate.connect(_on_post_migrate, dispatch_uid=f"enable_webhooks_post_migration")

def connect_webhook_signals():
    webhook_models = [Submission, TestResult, ReferenceSet, TestReference]

    for model in webhook_models:
        lower_name = model.__name__.lower()
        signals.post_save.connect(_on_model_save, sender=model, dispatch_uid=f"webhook_{lower_name}_save")
        signals.post_delete.connect(_on_model_delete, sender=model, dispatch_uid=f"webhook_{lower_name}_delete")

    signals.pre_migrate.connect(_on_pre_migrate, dispatch_uid=f"disable_webhooks_on_migration")
    signals.post_migrate.disconnect(dispatch_uid=f"enable_webhooks_post_migration")
