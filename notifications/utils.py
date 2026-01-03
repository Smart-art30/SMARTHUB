from django.core.mail import send_mail
from django.conf import settings 
from models import Notifications

def send_notification(user, title, message, email= False):
    Notification.objects.create(
        user=user,
        title = title,
        message=message
    )
    if email and user.email:
        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True

        )