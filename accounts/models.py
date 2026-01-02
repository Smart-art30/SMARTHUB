from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    #roles
    ROLES_CHOOCES = (
        ('superadmin', 'Super Admin'),
        ('chiefexercutiveofficer', 'C.E.O'),
        ('schooladmin', 'School Admin'),
        ('teacher', 'Teacher'),
        ('student', 'student'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length = 100, choices = ROLES_CHOOCES)
    school = models.ForeignKey(
        'schools.School',
        on_delete = models.CASCADE,
        blank = True,
        null = True,
        help_text = 'Assign User to a school'
    )
    phone = models.CharField(max_length = 20, blank = True, null = True)
    profile_image = models.ImageField(upload_to = 'profiles/',blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Subject(models.Model):
    #school = models.ForeignKey(School, on_delete = models.CASCADE)
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    name = models.CharField(max_length = 100)
    code = models.CharField(max_length = 20, blank = True, null =  True)
    assigned_teacher = models.ManyToManyField('User',limit_choices_to={'role': 'teacher'},blank = True)

    def __str__(self):
        return f'{self.name} ({self.school.name})'


class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role':'teacher'}

    )
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    employee_id=models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    date_joined= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

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
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
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
    max_mark = models.PositiveIntegerField(default=100)

    def __str__(self):
        return f'{self.subject.name} - {self.exam.name}'

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
        elif self.mark >= 50:
            return 'D'
        else:
            return 'E'
    def __str__(self):
        return f'{self.student} - {self.exam_subject} - {self.marks}'
        

class FeeStructure(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    student_class = models.ForeignKey('schools.SchoolClass', on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    year = models.IntegerField()

    def __str__(self):
        return f'{self.student_class} - {self.term} {self.year}'


class FeeItem(models.Model):
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100) # Tuition, Lunch, Transport
    amount = models.DecimalField(max_digits =  10, decimal_places = 2)

    def __str__(self):
        return  f'{self.name} - {self.amount}'

class Invoice(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    issued_date = models.DateField(auto_now_add=True)
    is_paid = models.BooleanField(default=False) 

    def total_amount(self):
        return sum(item.amount for item in self.fee_structure.items.all())
    def total_paid(self):
        return sum(payment.amount for payment in self.payments.all())
    def balance(self):
        return self.total_amount() - self.total_paid()
    def __str__(self):
        return f'Invoice - {self.student}'


class Payment(models.Model):
    Invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits= 10, decimal_places=2)
    payment_method = models.CharField(
        max_length =  20,
        choices =(
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('mpesa', 'Mpesa'),
        )
    )
    transaction_reference = models.CharField(max_length=100, blank= True, null=True)
    payment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.amount} - {self.payment_method}'

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES =[
        ('fee', 'Fee Riminder'),
        ('absense', 'Absense Alert'),
        ('exam', 'Exam Announcement Alert'),
        ('general', 'General Notice'),
    ]

    CHANNEL_CHOICES =[
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('in_app', 'In-App'),
    ]
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length = 20,
        choices = NOTIFICATION_TYPE_CHOICES
    )
    channel = models.CharField(
        max_length = 20,
        choices = CHANNEL_CHOICES
    )
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(null = True, blank = True)

    def __str__(self):
        return f'{self.title} ({self.channel})'

class CommunicationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    recieve_sms = models.BooleanField(default=True)
    recieve_email = models.BooleanField(default= True)
    recieve_in_app = models.BooleanField(default= True)

    def __str__(seld):
        return f'{self.user.username} Preferences'
