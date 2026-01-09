from django.urls import path
from .views import login_view, logout_view, register_view
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='signup'),
    path('accounts/register/', views.register_view, name='register'),  # <-- connect register view



]