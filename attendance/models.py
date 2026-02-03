from django.db import models
from django.utils import timezone
from students.models import Student
from teachers.models import Teacher
from schools.models import School, SchoolClass

class StudentAttendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    student_class = models.ForeignKey(
        SchoolClass, on_delete=models.SET_NULL, null=True
    )

    date = models.DateField(default=timezone.now)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='present'
    )

    marked_by = models.ForeignKey(
        Teacher, on_delete=models.SET_NULL, null=True, blank=True
    )

    marked_at = models.DateTimeField(auto_now=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'date'],
                name='unique_student_attendance_per_day'
            ),
        ]

    def __str__(self):
        return f"{self.student} | {self.date} | {self.status}"


        

class TeacherAttendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='teacher_attendance'
    )

    date = models.DateField(default=timezone.now)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='present'
    )

    marked_by = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_teacher_attendance'
    )

    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('teacher', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.teacher} | {self.date} | {self.status}"

