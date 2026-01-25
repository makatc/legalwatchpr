"""
Security middleware for rate limiting, request validation, and security headers.
"""
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting middleware using Django cache.
    Limits requests per IP address over a time window.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.rate_limit = getattr(settings, 'RATE_LIMIT_REQUESTS', 100)
        self.rate_window = getattr(settings, 'RATE_LIMIT_WINDOW', 60)  # seconds
    
    def process_request(self, request):
        """Check rate limit before processing request."""
        # Skip rate limiting for certain paths
        if self._should_skip_rate_limit(request):
            return None
        
        # Get client IP
        ip_address = self._get_client_ip(request)
        
        # Check rate limit
        if not self._check_rate_limit(ip_address):
            logger.warning(f"Rate limit exceeded for IP: {ip_address}")
            return JsonResponse(
                {'error': 'Rate limit exceeded. Please try again later.'},
                status=429
            )
        
        return None
    
    def _should_skip_rate_limit(self, request) -> bool:
        """Determine if rate limiting should be skipped for this request."""
        skip_paths = getattr(settings, 'RATE_LIMIT_SKIP_PATHS', [])
        return any(request.path.startswith(path) for path in skip_paths)
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip
    
    def _check_rate_limit(self, ip_address: str) -> bool:
        """
        Check if IP address is within rate limits.
        
        Args:
            ip_address: Client IP address
        
        Returns:
            True if within limits, False if exceeded
        """
        cache_key = f'rate_limit:{ip_address}'
        
        # Get current request count and timestamp
        data = cache.get(cache_key, {'count': 0, 'reset_time': time.time() + self.rate_window})
        
        # Reset if window expired
        if time.time() >= data['reset_time']:
            data = {'count': 0, 'reset_time': time.time() + self.rate_window}
        
        # Increment count
        data['count'] += 1
        
        # Update cache
        cache.set(cache_key, data, self.rate_window)
        
        # Check limit
        return data['count'] <= self.rate_limit


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    
    def process_response(self, request, response):
        """Add security headers to response."""
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        if not settings.DEBUG:
            response['Content-Security-Policy'] = "default-src 'self'"
        
        return response


class RequestValidationMiddleware(MiddlewareMixin):
    """
    Validate incoming requests for security issues.
    """
    
    def process_request(self, request):
        """Validate request before processing."""
        # Check content length
        max_size = getattr(settings, 'MAX_REQUEST_SIZE', 10 * 1024 * 1024)  # 10MB default
        content_length = request.META.get('CONTENT_LENGTH')
        
        if content_length and int(content_length) > max_size:
            logger.warning(f"Request too large: {content_length} bytes")
            return JsonResponse(
                {'error': 'Request entity too large'},
                status=413
            )
        
        # Validate user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent and not settings.DEBUG:
            logger.warning("Missing User-Agent header")
            return JsonResponse(
                {'error': 'Missing User-Agent header'},
                status=400
            )
        
        return None
