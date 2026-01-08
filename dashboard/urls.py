from django.urls import path
from . import views
from .views import dashboard_redirect
from django.contrib.auth import views as auth_views
from students.views import student_list, student_add



urlpatterns=(
    path('superadmin/', views.superadmin_dashboard, name = 'superadmin_dashboard'),
    path('schooladmin/', views.schooladmin_dashboard, name='schooladmin_dashboard'),
    path('teacher/', views.teacher_dashboard, name = 'teacher_dashboard'),
    path('student/', views.student_dashboard, name = 'student_dashboard'),
    path('parent/', views.parent_dashboard, name='parent_dashboard'),
    path('',dashboard_redirect, name='dashboard'),
    path('students/', student_list, name='student_list'),
    path('add/', student_add, name='student_add'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

  
    
)
