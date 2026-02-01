from django.urls import path
from . import views

app_name = 'teachers'

urlpatterns= [
    path('', views.teacher_list, name='teacher_list'),
    path('add/', views.teacher_add, name='teacher_add'),
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
    #path('add-teacher-subject/', views.add_teacher_subject, name='add_teacher_subject'),
    path('assign-teacher/', views.assign_teacher_subjects, name='assign_teacher_subject'),
    #path('assign-subjects/', views.assign_subjects_to_class, name='assign_subjects'),
    path('', views.teacher_list, name='teacher_list'),
    path('add/', views.teacher_add, name='teacher_add'),
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),   
    path('<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),  
    path('<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('assign/', views.assign_teacher_subjects, name='assign_teacher_subjects'),
    path('assign/', views.assign_teacher_subjects, name='assign_teacher_subjects'),
    path('assign/remove/<int:teacher_id>/<int:class_id>/', views.remove_teacher_subjects, name='remove_teacher_subjects'),
    path('assign/', views.assign_teacher_subjects, name='assign_teacher_subjects'),
    path('assign/remove_all/<int:teacher_id>/<int:class_id>/', views.remove_teacher_subjects, name='remove_teacher_subjects'),
    path('assign/remove/<int:assignment_id>/', views.remove_single_assignment, name='remove_single_assignment'),
    path('teachers/ajax-assign-subjects/', views.ajax_assign_subjects, name='ajax_assign_subjects'),


]


