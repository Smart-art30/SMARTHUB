from django.urls import path
from . import views
from .views import admin_class_marks,admin_class_list

app_name = 'academics'

urlpatterns = [

    # ===== ADMIN =====
    path('admin/classes/', admin_class_list, name='admin_class_list'),
    path('admin/class/<int:class_id>/marks/', admin_class_marks, name='admin_class_marks'),
    #path('admin/class/<int:class_id>/marks/pdf/', admin_class_marks_pdf, name='admin_class_marks_pdf'),

    # ===== SUBJECTS =====
    path('subjects/', views.subject_list, name='subject_list'),
    path('subject/add/', views.subject_add, name='subject_add'),
    path('subject/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subject/<int:pk>/delete/', views.subject_delete, name='subject_delete'),

    # ===== EXAMS =====
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_add, name='exam_add'),
    path('exam/<int:pk>/edit/', views.exam_edit, name='exam_edit'),
    path('exam/<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    path('exams/assign-subjects/', views.assign_subjects_to_exam, name='assign_subjects_to_exam'),
    path('exams/<int:exam_id>/assign-subjects/', views.exam_subject_add, name='exam_subject_add'),
    path('exam-subjects/<int:pk>/remove/', views.remove_exam_subject, name='remove_exam_subject'),

    # ===== MARKS (TEACHER) =====
    path('marks/classes/', views.select_classes, name='select_classes'),
    path('marks/classes/<int:class_id>/', views.class_overview, name='class_overview'),
    path('marks/classes/<int:class_id>/subject/<int:subject_id>/', views.select_exam, name='select_exam'),
    path('marks/classes/<int:class_id>/exam/<int:exam_id>/', views.enter_marks, name='enter_marks'),
    path('ajax/save-mark/', views.save_mark_ajax, name='save_mark_ajax'),

    # ===== REPORTS =====
    path('reports/class/<int:class_id>/', views.class_report, name='class_report'),
    path('reports/<int:student_id>/', views.student_report, name='student_report'),
    path('dashboard/reports/', views.report_list, name='report_list'),
    path('dashboard/reports/<int:student_id>/<int:exam_id>/', views.student_report, name='student_exam_report'),
]
