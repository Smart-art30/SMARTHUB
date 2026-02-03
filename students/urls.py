from django.urls import path
from . import views
from academics import views as academics_views 
app_name = 'students' 


urlpatterns=[
    path('add/', views.student_add, name='student_add'),

   
    path('parents/', views.parent_list, name='parent_list'),
    path('add_parents/', views.add_parent, name='add_parent'),

 
    path('class/<int:class_id>/download/', views.class_download, name='class_download'),

    path('<int:pk>/edit/', views.student_update, name='student_update'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
#===========================================================================================================#


    path('classes/', views.class_list, name='class_list'),
    path('classes/<int:pk>/', views.class_detail, name='class_detail'),
    path('classes/<int:pk>/download/', views.class_download, name='class_download'),

    path('add/', views.student_add, name='student_add'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/edit/', views.student_update, name='student_update'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),


   #======================================================================
   
    path('classes/', views.class_list, name='class_list'),
    path('classes/<int:pk>/', views.class_detail, name='class_detail'),
    path('classes/<int:pk>/download/', views.class_download, name='class_download'),

    path('add/', views.student_add, name='student_add'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/edit/', views.student_update, name='student_update'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    path("", views.student_list, name="student_list"),


    
]