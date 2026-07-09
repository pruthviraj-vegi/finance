import re
from django.conf import settings
from django.shortcuts import redirect

class LoginRequiredMiddleware:
    """
    Middleware that requires user authentication for all views,
    except for paths defined in settings.LOGIN_EXEMPT_URLS.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_urls = [re.compile(expr) for expr in getattr(settings, 'LOGIN_EXEMPT_URLS', [])]

    def __call__(self, request):
        if not request.user.is_authenticated:
            path = request.path_info.lstrip('/')
            # Check if the requested path is exempt
            if not any(pattern.match(path) for pattern in self.exempt_urls):
                return redirect(settings.LOGIN_URL)
        return self.get_response(request)
