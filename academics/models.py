from django.db import models
from schools.models import School, SchoolClass
from students.models import Student
from django.conf import settings

class Subject(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    name = models.CharField(max_length = 100)
    code = models.CharField(max_length = 20, blank = True, null =  True)
    assigned_teacher = models.ManyToManyField(

        settings.AUTH_USER_MODEL,
        related_name='subjects',
        limit_choices_to={'role': 'teacher'},
        blank = True
        )

    class Meta:
        unique_together =  ('school', 'code')

    def __str__(self):
        return f'{self.name} ({self.school.name})'


class Exam(models.Model):
    
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    
    name = models.CharField(max_length=100)
    term = models.CharField(max_length= 20)
    year = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} - {self.term} ({self.year})'

class ExamSubject(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    school_class = models.ForeignKey(
        SchoolClass, on_delete=models.CASCADE
    )
    max_mark = models.PositiveIntegerField(default=100)

    class Meta:
        unique_together = ('exam', 'subject', 'school_class')


class StudentMark(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE)
    marks = models.FloatField()

    class Meta:
        unique_together = ('student', 'exam_subject')

    def grade(self):
        if self.marks >= 80:
            return 'A'
        elif self.marks >= 70:
            return "B"
        elif self.marks >= 60:
            return 'C'
        elif self.marks >= 50:
            return 'D'
        else:
            return 'E'
    def __str__(self):
        return f'{self.student} - {self.exam_subject} - {self.marks}'
        