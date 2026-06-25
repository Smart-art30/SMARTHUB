from django.db import models
from schools.models import School, SchoolClass
from students.models import Student
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator



class AcademicTerm(models.Model):
    TERM_CHOICES = [
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'),
        ('Term 3', 'Term 3'),
    ]
    YEAR_CHOICES = [(y, y) for y in range(2020, 2090)]

    school = models.ForeignKey('schools.School', on_delete=models.CASCADE, default=1)
    year = models.IntegerField(choices=YEAR_CHOICES, default=2026)
    term = models.CharField(max_length=50, choices=TERM_CHOICES)
    is_active = models.BooleanField(default=False)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ('school', 'year', 'term')

    def __str__(self):
        return f'{self.term} - {self.year}'


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
        self.short_name = self.name[:4].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.school.name})'


class Exam(models.Model):
    

    EXAM_TYPE_CHOICES = [
        ('Opener', 'Opener'),
        ('Mid-term', 'Mid-term'),
        ('End-term', 'End-term'),
    ]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    term = models.ForeignKey(AcademicTerm, on_delete=models.CASCADE)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPE_CHOICES, default='Opener')
    name = models.CharField(max_length=100)
    max_mark = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('school', 'term', 'exam_type')

    def __str__(self):
        return f'{self.exam_type} - {self.term}'

class StudentMark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    school_class = models.ForeignKey(SchoolClass,on_delete=models.CASCADE,null=True,blank=True)
    #term = models.CharField(max_length=20)

    marks = models.PositiveIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ],
        null=True,
        blank=True
    )

    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facilitated_marks'
    )

    class Meta:
        unique_together = ('student', 'subject', 'exam')

    def grade(self):
        if self.marks >= 80:
            return 'Exeeding Expectation'
        elif self.marks >= 60:
            return 'Meeting Expectation'
        elif self.marks >= 40:
            return 'Approaching Expectation'
        else:
            return 'Below Expectation'


class ExamSubject(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('exam', 'school_class', 'subject')

    def __str__(self):
        return f'{self.exam} - {self.school_class} - {self.subject}'

