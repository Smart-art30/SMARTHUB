from django.core.mail import send_email 
from django.conf import settings

def send_email(subject, message, recipient_list):
    try:
        send_mail(
            subject = subject,
            message= message,
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list = recipient_list,
            fail_silently  = False
        )

        return True, None
    except Exeption as e:
        return False, str(e)