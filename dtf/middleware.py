
from django.utils import timezone
from django.conf import settings

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # TODO: get timezone from user profile when users have been implemented.
        timezone.activate(settings.DTF_DEFAULT_DISPLAY_TIME_ZONE)
        return self.get_response(request)
