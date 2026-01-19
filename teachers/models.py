from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from schools.models import SchoolClass, School
from academics.models import Subject



class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'}
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('Male','Male'),('Female','Female'),('Other','Other')], blank=True)
    designation = models.CharField(max_length=50, blank=True, null=True)
    qualification = models.CharField(max_length=100, blank=True, null=True)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    is_class_teacher = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='teachers/', blank=True, null=True)
    is_approved = models.BooleanField(default=True)
    subjects = models.ManyToManyField(Subject, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class TeacherClass(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name="assigned_classes"
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE
    )
    class Meta:
        unique_together = ('teacher', 'school_class')

    def __str__(self):
        return f'{self.teacher} -> {self.school_class}'
