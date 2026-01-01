from .email_service import send_email
from .sms_service import send_sms
from communication. models imort MessageLog

def disatch_notification(notification, recipient):
    '''
    notification: Notification object
    recipeints: list of dicts -> {
    'name,: ""
    'email': ""
    'phone': ""}
    '''

    for recipient in recipeints:
        success = False
        error  = None 

        if notification.channel == 'email':
            notification.title,
            notification.message,
            [recipient['email']]

        elif notification.channel == 'sms':
            success,error = send_sms(
                recipient['phone'],
                notification.message
            )

        MessageLog.objects.create(
            notification =  notification,
            recipient_name=recipeint['name'],
            recipent_contact=recipeint.get('email') or recipeint.get('phone')
            status = 'sent' if success else 'failed',
            error_message= error
        )





