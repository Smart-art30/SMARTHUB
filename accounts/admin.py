from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username','email','role','school','is_staff','is_active')
    list_filter = ('role','is_staff', 'is_active')
    fieldsets= (
        (None, {'fields': ('username', 'email','password','role')}),
        ('permissions',{'fields':('is_staff','is_active','is_superuser','groups','user_permissions')}),
    )
    add_fieldsets =(
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email','password1','password2','role','school','is_staff','is_active')
        }),
    )
    search_fields = ('email', 'username')
    ordering = ('username',)
    filter_horizontal = ('groups','user_permissions',) 

admin.site.register(User, CustomUserAdmin)



