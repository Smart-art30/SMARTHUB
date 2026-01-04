from django.urls import path
from . import views

urlpatterns= [
    path('', views.teacher_list, name='teacher_list'),
    path('add/', views.teacher_add, name='teacher_add'),
    path('<int:pk', views.teacher_detail, name='teacher_detail'),
]