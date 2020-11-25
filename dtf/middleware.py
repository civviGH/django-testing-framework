
from django.utils import timezone

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate("Europe/Berlin") # TODO: get user timezone
        return self.get_response(request)
