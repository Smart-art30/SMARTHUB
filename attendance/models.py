from django.db import models
from django.utils import timezone
from students.models import Student
from teachers.models import Teacher
from schools.models import School, SchoolClass


class StudentAttendance(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    student_class= models.ForeignKey('schools.SchoolClass', on_delete=models.SET_NULL, null=True)
    date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length= 10,
        choices =(('present','Present'),('absent', 'Absent'),('late','Late')), default='present'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student','date')

    def __str__(self):
        return f'{self.student} - {self.date} - {self.status}'

class TeacherAttendance(models.Model):
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.CASCADE)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    date= models.DateField(default=timezone.now)
    status= models.CharField(
        max_length=10,
        choices=(('present','Present'),('abasent','Absent'),('late','Late')),default= 'present'

    )
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('teacher','date')

    def __str__(self):
        return f"{self.teacher} - {self.date} - {self.status}"

