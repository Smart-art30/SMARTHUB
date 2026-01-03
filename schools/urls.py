from django.urls import Path
from .views import school_signup

urlpatterns=[
    path('signup/', school_signup, name = 'school_signup'),
]