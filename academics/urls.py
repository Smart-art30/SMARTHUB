from django.urls import path
from . import views

urlpatterns=[
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/',views.subjects_add, name='subject_add'),
]