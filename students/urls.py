from django.urls import path
from . import views
from academics import views as academics_views 
app_name = 'students' 


urlpatterns=[
    path('', views.student_list, name='student_list'),
    path('add/', views.student_add, name='student_add'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('parents/', views.parent_list, name= 'parent_list'),
    path('add_parents/', views.add_parent, name = 'add_parent'),
    path('<int:pk>/edit/', views.student_update, name='student_update'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('class/<int:class_id>/download/', views.class_download, name='class_download'),



   

    
]