from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    
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






class CommunicationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    recieve_sms = models.BooleanField(default=True)
    recieve_email = models.BooleanField(default= True)
    recieve_in_app = models.BooleanField(default= True)

    def __str__(seld):
        return f'{self.user.username} Preferences'
