from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns= [
    path('', views.teacher_list, name='teacher_list'),
    path('add/', views.teacher_add, name='teacher_add'),
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('add-teacher-subject/', views.add_teacher_subject, name='add_teacher_subject'),
    path('assign-teacher/', views.assign_teacher_subject, name='assign_teacher_subject'),
    path('assign-subjects/', views.assign_subjects_to_class, name='assign_subjects'),


]