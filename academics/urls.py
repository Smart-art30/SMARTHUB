from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
   
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_add, name='subject_add'),

   
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_add, name='exam_add'),
    path('exams/<int:exam_id>/assign-subjects/', views.exam_subject_add, name='exam_subject_add'),
    path('marks/classes/<int:class_id>/', views.select_class, name='select_class'),

    path('marks/classes/', views.select_class, name='select_class'),  
    path('marks/classes/<int:class_id>/', views.class_overview, name='class_overview'),  
    path('marks/classes/<int:class_id>/subject/<int:subject_id>/', views.select_exam, name='select_exam'), 
    path('marks/exam/<int:exam_id>/', views.enter_marks, name='enter_marks'), 
    
    path('marks/classes/<int:class_id>/', views.select_class, name='select_class'),
    path('assign-teacher/', views.assign_teacher, name='assign_teacher'),
    path('dashboard/reports/', views.report_list, name='report_list'),
    path('dashboard/reports/<int:student_id>/<int:exam_id>/', views.student_report, name='student_report'),
    path('select-classes/', views.select_marks_classes, name='select_classes'),
    path('enter-marks/', views.enter_marks_multi, name='enter_marks_multi'),
]
