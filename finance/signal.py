from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment

@receiver(post_save, sender=Payment)
def auto_update_invoice(sender, instance, **kwargs):
    if instance.status == 'confirmed':
        instance.invoice.update_payment_status()
