from django.urls import path
from . import views

urlpatterns = [
   
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),

  
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_add, name='exam_add'),
    path('exams/entry/', views.mark_entry, name='mark_entry'),

    
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),

    
    path('dashboard/reports/', views.report_list, name='report_list'),

    path('dashboard/reports/<int:student_id>/<int:exam_id>/', views.student_report, name='student_report'),
]
