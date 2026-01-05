from django.urls import path
from .views import school_signup
from . import views

urlpatterns=[
    path('signup/', school_signup, name = 'school_signup'),
    path('classses/', views.class_list, name='class_list'),
    path('classes/add/', views.class_add, name='class_add'),
]