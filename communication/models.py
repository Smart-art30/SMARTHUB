from django.db import models


class MessageLog(models.Model):
    STATUS_CHOICES =[
        ('pending','Pending'),
        ('sent', 'Sent'),
        ('failed', 'Field'),

    ]
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    recipent_name = models.CharField(max_length=200)
    recipent_contact = models.CharField(max_length = 100)
    satus  = models.CharField(
        max_length =  20,
        choices = STATUS_CHOICES,
        default = 'pending'
    )
    error_message = models.TextField(blank=True, null = True)
    sent_at  = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'{self.recipient_name} - {self.status}'

