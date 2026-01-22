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
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    
    path('', include(('dashboard.urls', 'dashboard'), namespace='dashboard')),

    path('schools/', include(('schools.urls', 'schools'), namespace='schools')),
    path('students/', include(('students.urls', 'students'), namespace='students')),

    
    path('teachers/', include(('teachers.urls', 'teachers'), namespace='teachers')),

    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    path('finance/', include(('finance.urls', 'finance'), namespace='finance')),
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
    path('academics/', include(('academics.urls', 'academics'), namespace='academics')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

