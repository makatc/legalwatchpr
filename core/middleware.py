from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache

class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        return None

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        return response

class RequestValidationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        return None
