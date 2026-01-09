from django.db import models
from django.conf import settings
from schools.models import School, SchoolClass

User =  settings.AUTH_USER_MODEL

class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'}
    )
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    student_class = models.ForeignKey('schools.SchoolClass', on_delete=models.SET_NULL, null=True)
    admission_number = models.CharField(max_length = 30, unique= True)
    date_of_birth = models.DateField(blank=True, null = True)
    photo = models.ImageField(upload_to='students/photos',blank=True, null=True)
    gender = models.CharField(
        max_length = 10,
        choices = (('male','Male'), ('female','Female')),
        blank = True,
        null = True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.admission_number}"

    class Meta:
        ordering = ['admission_number']
        constraints = [
            models.UniqueConstraint(
                fields=['school', 'admission_number'],
                name='unique_admission_per_school'
            )
        ]

class Parent(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'parent'}
    )
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    students = models.ManyToManyField(Student, related_name = 'parents')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
