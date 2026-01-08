from django.urls import path
from .views import school_signup
from .views import add_class, class_list, edit_class, delete_class

urlpatterns=[
    path('signup/', school_signup, name = 'school_signup'),
    path('classses/', class_list, name='class_list'),
    path('classes/add/', add_class, name='add_class'),
]