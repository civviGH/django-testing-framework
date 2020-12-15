from django.apps import AppConfig


class DtfConfig(AppConfig):
    name = 'dtf'
    verbose_name = 'Django Testing Framework'

    def ready(self):
        from .webhooks import connect_webhook_signals
        connect_webhook_signals()