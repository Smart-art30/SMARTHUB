from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from schools.models import SchoolClass


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role':'teacher'}

    )
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    employee_id=models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_joined= models.DateTimeField(auto_now_add=True)

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
