from django.urls import path
from . import views
from .views import dashboard_redirect, home
from django.contrib.auth import views as auth_views


urlpatterns=(
    path('', home, name= 'home'),
    path('superadmin/', views.superadmin_dashboard, name = 'superadmin_dashboard'),
    path('schooladmmin/', views.schooladmin_dashboard, name = 'schooladmin_dashboard'),
    path('teacher/', views.teacher_dashboard, name = 'teacher_dashboard'),
    path('student/', views.student_dashboard, name = 'student_dashboard'),
    path('parents/', views.parent_dashboard, name = 'parent_dashboard'),
    path('',dashboard_redirect, name='dashboard'),
    
)
