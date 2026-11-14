from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

DEVELOPER, AUDITOR, ADMIN = "developer", "auditor", "admin"


def role_required(*roles):
    """Use on every view except login and logout.

    Not logged in -> login page (302). Wrong role -> 403.
    """
    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view(request, *args, **kwargs)
        return login_required(wrapper)
    return decorator
