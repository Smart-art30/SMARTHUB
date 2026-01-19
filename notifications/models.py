from django.db import models
from django.conf import settings


User = settings.AUTH_USER_MODEL

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES =[
        ('fee', 'Fee Reminder'),
        ('absence', 'Absence Alert'),
        ('exam', 'Exam Announcement Alert'),
        ('general', 'General Notice'),
    ]

    CHANNEL_CHOICES =[
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('in_app', 'In-App'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    notification_type = models.CharField(
        max_length = 20,
        choices = NOTIFICATION_TYPE_CHOICES,
        db_index = True
    )
    channel = models.CharField(
        max_length = 20,
        choices = CHANNEL_CHOICES
    )
    scheduled_for = models.DateTimeField(
        null = True,
        blank = True,
        help_text="leave empty to send immediately"
        )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.get_channel_display()})'
