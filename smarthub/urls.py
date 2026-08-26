from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard.views import dashboard_redirect

urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        'dashboard/',
        include(('dashboard.urls', 'dashboard'), namespace='dashboard')
    ),

    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "accounts/",
        include(("accounts.urls", "accounts"), namespace="accounts")
    ),

    path(
        'schools/',
        include(('schools.urls', 'schools'), namespace='schools')
    ),

    path(
        'students/',
        include(('students.urls', 'students'), namespace='students')
    ),

    path(
        'teachers/',
        include(('teachers.urls', 'teachers'), namespace='teachers')
    ),

    path(
        'finance/',
        include(('finance.urls', 'finance'), namespace='finance')
    ),

    path(
        'attendance/',
        include(('attendance.urls', 'attendance'), namespace='attendance')
    ),

    path(
        'academics/',
        include(('academics.urls', 'academics'), namespace='academics')
    ),

    path('', dashboard_redirect, name='home'),
]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)