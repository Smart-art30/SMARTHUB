from django.db import models
from schools.models import School, SchoolClass
from students.models import Student
from django.conf import settings


class Subject(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True, null=True)
    short_name = models.CharField(max_length=10, blank=True) 
    assigned_teacher = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='subjects',
        limit_choices_to={'role': 'teacher'},
        blank=True
    )

    class Meta:
        unique_together = ('school', 'code')

    def save(self, *args, **kwargs):
        if not self.short_name:
            self.short_name = self.name[:4].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.school.name})'





class Exam(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    term = models.CharField(max_length=20)
    year = models.IntegerField()
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
   
    max_mark = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'school_class', 'term', 'year', 'name')

    def __str__(self):
        return f'{self.name} - {self.term} ({self.year})'


class StudentMark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE) 
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)  
    marks = models.FloatField()
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use this instead of User
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        unique_together = ('student', 'exam', 'subject')

    def grade(self):
        if self.marks >= 80:
            return 'A'
        elif self.marks >= 70:
            return 'B'
        elif self.marks >= 60:
            return 'C'
        elif self.marks >= 50:
            return 'D'
        else:
            return 'E'

    def __str__(self):
        return f'{self.student} - {self.exam} - {self.subject} - {self.marks}'

class ExamSubject(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('exam', 'school_class', 'subject')

    def __str__(self):
        return f'{self.exam} - {self.school_class} - {self.subject}'


class AcademicTerm(models.Model):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.name
