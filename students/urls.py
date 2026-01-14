from django.urls import path
from . import views

urlpatterns=[
    path('', views.student_list, name='student_list'),
    path('add/', views.student_add, name='student_add'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('parents/', views.parent_list, name= 'parent_list'),
    path('add_parents/', views.add_parent, name = 'add_parent'),
]