from django.contrib import admin
from teachers.models import Teacher, TeacherClass
from schools.models import School


admin.site.register(TeacherClass)





@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'school', 'employee_id', 'is_approved')
    list_filter = ('is_approved', 'school')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')

    # Fields to show in the form
    fields = ('user', 'school', 'employee_id', 'phone', 'designation', 'qualification',
              'specialization', 'is_class_teacher', 'profile_picture', 'is_approved')

    actions = ['approve_teachers']

    def approve_teachers(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} teacher(s) approved successfully.")
    approve_teachers.short_description = "Approve selected teachers"