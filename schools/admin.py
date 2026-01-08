from django.contrib import admin
from .models import SchoolClass, SubscriptionPlan

from .models import School, SchoolClass
admin.site.register(School)
admin.site.register(SubscriptionPlan)
#admin.site.register(SchoolClass)

@admin.register(SchoolClass)

class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'section','stream', 'school')
    list_filter  = ('school',)
    search_fields = ('name', 'stream', 'section')
    def save_model(self, request, obj, form, change):

        if hasattr(request.user, 'school'):
            obj.school = request.user.school
            super().save_model(request, obj, form, change)