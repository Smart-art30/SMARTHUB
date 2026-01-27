from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # ----- Subjects -----
    path('subjects/', views.subject_list, name='subject_list'),
    path('subject/add/', views.subject_add, name='subject_add'),
    path('subject/<int:pk>/edit/', views.subject_edit, name='subject_edit'),
    path('subject/<int:pk>/delete/', views.subject_delete, name='subject_delete'),

    # ----- Exams -----
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_add, name='exam_add'),
    path('exams/<int:exam_id>/assign-subjects/', views.exam_subject_add, name='exam_subject_add'),
    path('exams/<str:name>/<str:term>/<int:year>/marks/', views.enter_marks_group, name='enter_marks_group'),
    path('exams/<str:name>/<str:term>/<int:year>/edit/', views.exam_update_group, name='exam_update_group'),
    path('exams/<str:name>/<str:term>/<int:year>/delete/', views.exam_delete_group, name='exam_delete_group'),

    # ----- Marks -----
    path('marks/classes/', views.select_class, name='select_classes'),  # choose class first
    path('marks/classes/<int:class_id>/', views.class_overview, name='class_overview'),
    path('marks/classes/<int:class_id>/subject/<int:subject_id>/', views.select_exam, name='select_exam'),
    path('marks/classes/<int:class_id>/exam/<int:exam_id>/', views.enter_marks, name='enter_marks'),  # fixed
    path('marks/exam/multi/', views.enter_marks_multi, name='enter_marks_multi'),

    # ----- Reports -----
    path('reports/<int:student_id>/', views.student_report, name='student_report'),
    path('dashboard/reports/', views.report_list, name='report_list'),
    path('dashboard/reports/<int:student_id>/<int:exam_id>/', views.student_report, name='student_exam_report'),
    path('consolidated-report/', views.consolidated_student_report, name='consolidated_report'),

    # ----- Teachers -----
    path('assign-teacher/', views.assign_teacher, name='assign_teacher'),
    path('ajax/save-mark/', views.save_mark_ajax, name='save_mark_ajax'),
]
