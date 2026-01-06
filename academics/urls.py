from django.urls import path
from . import views
from schools.views import school_list, school_detail

urlpatterns=[
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/',views.subjects_add, name='subject_add'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_add, name='exam_add'),
    path('exams/entry', views.mark_entry, name='mark_entry'),
    path('report/<int:student_id>/<int:exam_id>/', views.student_report, name='student_report'),
]