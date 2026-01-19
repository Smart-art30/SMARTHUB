from django.urls import path
from . import views
app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_list, name='attendance_list'),
    path('add/', views.attendance_add, name='attendance_add'),
    path('<int:pk>/', views.attendance_detail, name='attendance_detail'),
    path('<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    path('bulk/', views.bulk_attendance, name='bulk_attendance'),
    path('report/student/<int:student_id>/', views.student_attendance_report, name='student_attendance_report'),
    path('report/class/<int:class_id>/', views.class_attendance_report, name='class_attendance_report'),
    



]
