from django.contrib import admin
from .models import Subject, Exam, StudentMark


admin.site.register(Subject)
admin.site.register(Exam)

admin.site.register(StudentMark)