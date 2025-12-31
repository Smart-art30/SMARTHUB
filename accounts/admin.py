from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, School, SchoolClass, Subject, Student, Parent, Teacher, StudentAttendance, TeacherAttendance, Exam, ExamSubject, StudentMark, FeeStructure, FeeItem,Invoice, Payment

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
admin.site.register(School)
admin.site.register(SchoolClass)
admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(Parent)
admin.site.register(Teacher)
admin.site.register(StudentAttendance)
admin.site.register(TeacherAttendance)
admin.site.register(Exam)
admin.site.register(ExamSubject)
admin.site.register(StudentMark)
admin.site.register(FeeStructure)
admin.site.register(FeeItem)
admin.site.register(Invoice)
admin.site.register(Payment)


