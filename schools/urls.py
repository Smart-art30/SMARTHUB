from django.urls import path
from .views import school_signup
from .views import add_class, class_list, edit_class, delete_class
from . import views

urlpatterns=[
    path('signup/', school_signup, name = 'school_signup'),
    path('classes/', views.class_list, name='class_list'), 
    path('classes/add/', add_class, name='add_class'),
    path('classes/add/', views.add_class, name='add_class'),
    path('classes/', views.class_list, name='class_list'),
    path('classes/add/', views.add_class, name='add_class'),
    path('classes/edit/<int:class_id>/', views.edit_class, name='edit_class'),
    path('classes/delete/<int:class_id>/', views.delete_class, name='delete_class'),



]