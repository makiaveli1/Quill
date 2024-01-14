from django.db import transaction
from django.shortcuts import render, redirect, reverse, get_object_or_404, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
import stripe
import json
import logging

from bag.context_processors import bag_contents
from products.models import Product
from profiles.models import Profile
from profiles.forms import ProfileForm
from .forms import OrderForm
from .models import Order, OrderLineItem

# Set up logging
logger = logging.getLogger(__name__)

# Cache Checkout Data


@require_POST
def cache_checkout_data(request):
    try:
        pid = request.POST.get('client_secret').split('_secret')[0]
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.PaymentIntent.modify(pid, metadata={
            'bag': json.dumps(request.session.get('bag', {})),
            'save_info': request.POST.get('save_info'),
            'username': request.user.username,
        })
        return HttpResponse(status=200)
    except Exception as e:
        messages.error(
            request, """Your payment cannot be processed right now.
            Please try again later.""")
        return HttpResponse(content=e, status=400)

# Checkout


def checkout(request):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe_total = 0  # Initialize stripe_total at the beginning

    if request.method == 'POST':
        bag = request.session.get('bag', {})
        order_form = OrderForm(request.POST)

        if order_form.is_valid():
            order = order_form.save(commit=False)
            payment_intent_id = request.POST.get('payment_intent_id', None)

            if payment_intent_id:
                try:
                    payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                    if payment_intent.status == 'succeeded':
                        order.stripe_pid = payment_intent_id
                        order.original_bag = json.dumps(bag)
                        order.save()

                        for item_id, quantity in bag.items():
                            product = get_object_or_404(Product, pk=item_id)
                            order_line_item = OrderLineItem(
                                order=order,
                                product=product,
                                quantity=quantity,
                            )
                            order_line_item.save()

                        del request.session['bag']
                        return redirect(reverse('checkout_success', args=[order.order_number]))
                    else:
                        messages.error(request, "Payment was not successful, please try again.")
                except stripe.error.StripeError as e:
                    messages.error(request, f"An error occurred: {e.user_message}")
            else:
                messages.error(request, "No payment information found, please try again.")
        else:
            messages.error(request, "There was an error with your form. Please check your information.")

    else:
        # Handling GET request
        bag = request.session.get('bag', {})
        if not bag:
            messages.error(request, "Your bag is empty.")
            return redirect(reverse('products'))

        total = 0
        for item_id, quantity in bag.items():
            product = get_object_or_404(Product, pk=item_id)
            total += quantity * product.price

        stripe_total = round(total * 100)  # Stripe requires the amount to be in cents

        order_form = OrderForm()
        if request.user.is_authenticated:
            try:
                profile = Profile.objects.get(user=request.user)
                initial_data = {
                    'full_name': profile.user.get_full_name(),
                    'email': profile.user.email,
                    'phone_number': profile.default_phone_number,
                    'country': profile.default_country,
                    'post_code': profile.default_post_code,
                    'town_or_city': profile.default_town_or_city,
                    'address_line1': profile.default_address_line1,
                    'address_line2': profile.default_address_line2,
                    'county_or_state': profile.default_county_or_state,
                    
                }
                order_form = OrderForm(initial=initial_data)
            except Profile.DoesNotExist:
                order_form = OrderForm()

    intent = None
    if stripe_total > 0:
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY,
        )

    context = {
        'order_form': order_form,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
        'client_secret': intent.client_secret if intent else None,
    }

    return render(request, 'checkout/checkout.html', context)

# Checkout Success


def checkout_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)

    if request.user.is_authenticated:
        profile = Profile.objects.get(user=request.user)
        order.user_profile = profile
        order.save()

        if request.session.get('save_info'):
            profile_data = {
                'default_phone_number': order.phone_number,
                'default_country': order.country,
                'default_post_code': order.post_code,
                'default_town_or_city': order.town_or_city,
                'default_address_line1': order.address_line1,
                'default_address_line2': order.address_line2,
                'default_county_or_state': order.county_or_state,
            }
            profile_form = ProfileForm(profile_data, instance=profile)
            if profile_form.is_valid():
                profile_form.save()

    messages.success(request, f'''Order successfully processed!
                     Your order number is {
                     order_number}.
                     A confirmation email will be sent to {order.email}.''')

    if 'bag' in request.session:
        del request.session['bag']

    template = 'checkout/checkout_success.html'
    context = {
        'order': order,
    }

    return render(request, template, context)
