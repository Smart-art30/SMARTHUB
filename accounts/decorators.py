from django.core.exceptions import PermissionDenied
from teachers.models import Teacher
from students.models import Student

def role_required(*allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.role not in allowed_roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator




def role_required(*allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):

            if request.user.role not in allowed_roles:
                raise PermissionDenied

        
            if 'teacher' in allowed_roles:
                if not hasattr(request.user, 'teacher'):
                    raise PermissionDenied("Teacher profile not created")

           
            if 'student' in allowed_roles:
                if not hasattr(request.user, 'student'):
                    raise PermissionDenied("Student profile not created")

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
