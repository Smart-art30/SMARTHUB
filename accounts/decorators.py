from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

def role_required(*allowed_roles):
    """
    Allows access to users with specified roles or superusers.
    Checks for required related profiles (teacher/student).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = request.user

          
            if not user.is_authenticated:
                raise PermissionDenied

            if not (user.is_superuser or user.role in allowed_roles):
                raise PermissionDenied

           
            if 'teacher' in allowed_roles and hasattr(user, 'teacher'):
                if not user.teacher.is_approved:
                    return render(request, 'dashboard/profile_pending.html', {
                        'message': 'Your teacher profile is pending admin approval.'
                    })
               
            elif 'teacher' in allowed_roles and 'teacher' in user.role:
               
                return render(request, 'dashboard/profile_pending.html', {
                    'message': 'Teacher profile not created. Contact admin.'
                })

            if 'student' in allowed_roles and not hasattr(user, 'student'):
                return render(request, 'dashboard/profile_pending.html', {
                    'message': 'Student profile not created.'
                })

            if 'parent' in allowed_roles and not hasattr(user, 'parent'):
                return render(request, 'dashboard/profile_pending.html', {
                    'message': 'Parent profile not created.'
                })

          
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
