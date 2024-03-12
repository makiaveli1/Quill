from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderLineItem
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

@receiver(post_save, sender=OrderLineItem)
def update_on_save(sender, instance, created, **kwargs):
    instance.order.update_total()
    # Send email after saving if necessary
    subject = 'Your Order Update'
    message = render_to_string('email/order_update_email.txt', {'order': instance.order})
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.order.email])

@receiver(post_delete, sender=OrderLineItem)
def update_on_delete(sender, instance, **kwargs):
    instance.order.update_total()
    # Send email after deletion if necessary
    subject = 'Your Order Update'
    message = render_to_string('email/order_update_email.txt', {'order': instance.order})
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.order.email])
