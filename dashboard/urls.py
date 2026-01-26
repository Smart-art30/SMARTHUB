from django.urls import path
from . import views
from students.views import student_list, student_add
from academics.views import student_report

app_name = 'dashboard'  # Important for namespacing

urlpatterns = [
    # Redirect based on role
    path('', views.dashboard_redirect, name='dashboard_redirect'),

    # Dashboards
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('schooladmin/', views.schooladmin_dashboard, name='schooladmin_dashboard'),
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('parent/', views.parent_dashboard, name='parent_dashboard'),

    # Teacher profile
    path('teacher/profile/edit/', views.teacher_profile_edit, name='teacher_profile_edit'),

    # Students
    path('students/', student_list, name='student_list'),
    path('students/add/', student_add, name='student_add'),

    # Student reports
    path(
        'students/reports/<int:student_id>/<int:exam_id>/',
        student_report,
        name='student_report'
    ),
]
