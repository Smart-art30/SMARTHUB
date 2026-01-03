from django.contrib import admin
from .models import Subject,Exam, ExamSubject, StudentMark

admin.site.register(Subject)
admin.site.register(Exam)
admin.site.register(ExamSubject)
admin.site.register(StudentMark)