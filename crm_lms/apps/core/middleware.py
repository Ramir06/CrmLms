from django.middleware.csrf import CsrfViewMiddleware


class DevCsrfMiddleware(CsrfViewMiddleware):
    """Dev-only: trust any localhost origin regardless of port."""

    def _origin_verified(self, request):
        origin = request.META.get('HTTP_ORIGIN', '')
        if origin.startswith('http://127.0.0.1:') or origin.startswith('http://localhost:'):
            return True
        return super()._origin_verified(request)


class RoleMiddleware:
    """Attach role flags to the request object for easy template/view access."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.is_superadmin = request.user.role == 'superadmin'
            request.is_admin = request.user.role in ('admin', 'superadmin')
            request.is_mentor = request.user.role == 'mentor'
            request.is_student = request.user.role == 'student'
        else:
            request.is_superadmin = False
            request.is_admin = False
            request.is_mentor = False
            request.is_student = False

        return self.get_response(request)
