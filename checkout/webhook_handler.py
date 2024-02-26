import json
import logging
import time
from django.http import HttpResponse
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderLineItem
import stripe
from products.models import Product
from profiles.models import Profile
# Import settings for email
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

# Setup logging
logger = logging.getLogger(__name__)


class StripeWH_Handler:
    """
    Handle Stripe Webhooks
    """

    def __init__(self, request):
        self.request = request

    @staticmethod
    def _send_confirmation_email(order):
        cust_email = order.email
        subject = render_to_string(
            'checkout/confirmation_emails/confirmation_email_subject.txt',
            {'order': order})
        body = render_to_string(
            'checkout/confirmation_emails/confirmation_email_body.txt',
            {'order': order, 'contact_email': settings.DEFAULT_FROM_EMAIL})

        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [cust_email])

    def handle_event(self, event):
        logger.info(f'Unhandled webhook received: {event["type"]}')
        return HttpResponse(content=f'Unhandled Webhook received: {event["type"]}', status=200)

    def handle_payment_intent_succeeded(self, event):
        intent = event.data.object
        pid = intent.id
        bag = intent.metadata.bag
        save_info = intent.metadata.save_info

        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            stripe_charge = stripe.Charge.retrieve(intent.latest_charge)
        except Exception as e:
            logger.error(f"Error retrieving charge: {e}")
            return HttpResponse(content=f'Error: {e}', status=500)

        billing_details = stripe_charge.billing_details
        shipping_details = intent.shipping
        grand_total = round(stripe_charge.amount / 100, 2)

        for field, value in shipping_details.address.items():
            if value == "":
                shipping_details.address[field] = None

        profile = None
        username = intent.metadata.username
        if username != 'AnonymousUser':
            profile = Profile.objects.get(user__username=username)
            if save_info:
                profile.update_default_shipping_details(shipping_details)
                profile.save()

        order_exists = False
        attempt = 1
        while attempt <= 5:
            try:
                order = Order.objects.get(
                    full_name__iexact=shipping_details.name,
                    email__iexact=billing_details.email,
                    phone_number__iexact=shipping_details.phone,
                    country__iexact=shipping_details.address.country,
                    post_code__iexact=shipping_details.address.postal_code,
                    town_or_city__iexact=shipping_details.address.city,
                    address_line1__iexact=shipping_details.address.line1,
                    address_line2__iexact=shipping_details.address.line2,
                    county_or_state__iexact=shipping_details.address.state,
                    grand_total=grand_total,
                    original_bag=bag,
                    stripe_pid=pid,
                )
                order_exists = True
                break
            except Order.DoesNotExist:
                attempt += 1
                time.sleep(1)

        if order_exists:
            self._send_confirmation_email(order)
            return HttpResponse(content=f'Webhook received: {event["type"]} | SUCCESS: Verified order already in database', status=200)
        else:
            try:
                order = self._create_order(
                    intent, profile, billing_details, shipping_details, bag, pid, grand_total)
                for item_id, quantity in json.loads(bag).items():
                    self._create_order_line_item(order, item_id, quantity)
            except Exception as e:
                logger.error(f"Error creating order: {e}")
                return HttpResponse(content=f'Webhook received: {event["type"]} | ERROR: {e}', status=500)

        self._send_confirmation_email(order)
        return HttpResponse(content=f'Webhook received: {event["type"]} | SUCCESS: Created order in webhook', status=200)

    def handle_payment_intent_payment_failed(self, event):
        logger.info(f'Payment intent failed webhook received: {event["type"]}')
        return HttpResponse(content=f'Webhook received: {event["type"]}', status=200)

    def _create_order(self, intent, profile, billing_details, shipping_details, bag, pid, grand_total):
        order = Order.objects.create(
            full_name=shipping_details.name,
            user_profile=profile,
            email=billing_details.email,
            phone_number=shipping_details.phone,
            country=shipping_details.address.country,
            post_code=shipping_details.address.postal_code,
            town_or_city=shipping_details.address.city,
            address_line1=shipping_details.address.line1,
            address_line2=shipping_details.address.line2,
            county_or_state=shipping_details.address.state,
            original_bag=bag,
            stripe_pid=pid,
            grand_total=grand_total
        )
        return order

    def _create_order_line_item(self, order, item_id, quantity):
        product = Product.objects.get(id=item_id)
        if isinstance(quantity, int):
            OrderLineItem.objects.create(
                order=order, product=product, quantity=quantity)

# Django signal to send confirmation email after order is saved


@receiver(post_save, sender=Order)
def order_saved(sender, instance, **kwargs):
    StripeWH_Handler._send_confirmation_email(instance)
