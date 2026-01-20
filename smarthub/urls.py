"""
URL configuration for smarthub project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
#from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views




urlpatterns = [
    path('', include('dashboard.urls')),
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('schools/', include('schools.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('finance/', include('finance.urls')),
    path('accounts/', include('accounts.urls')), 
    path('attendance/', include('attendance.urls')),
    path('academics/', include('academics.urls', namespace='academics')), 
    path('teachers/', include('teachers.urls', namespace='teachers')),
    path('schooladmin/', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
