from django.db import transaction
from django.shortcuts import render, redirect, reverse, get_object_or_404, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
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
        logger.info("Processing payment...")
        client_secret = request.POST.get('client_secret')
        if not client_secret:
            logger.error("Missing 'client_secret' in the request.")
            raise ValueError("Missing 'client_secret' in the request.")
        
        pid = client_secret.split('_secret')[0]
        if not pid.startswith('pi_'):
            logger.error(f"Invalid 'client_secret' value: {client_secret}")
            raise ValueError("Invalid 'client_secret' value.")

        stripe.api_key = settings.STRIPE_SECRET_KEY
        save_info = request.POST.get('save_info', 'False').lower() == 'true'
        stripe.PaymentIntent.modify(pid, metadata={
            'bag': json.dumps(request.session.get('bag', {})),
            'save_info': json.dumps(save_info),
            'username': request.user.get_username() if request.user.is_authenticated else 'Anonymous',
        })

        logger.info("PaymentIntent modified successfully")
        return JsonResponse({'status': 'success'}, status=200)
    except Exception as e:
        logger.error(f"Error processing payment: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


from django.shortcuts import render, redirect, reverse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
import stripe

from .forms import OrderForm
from .models import Order, OrderLineItem
from products.models import Product
from profiles.models import Profile

stripe.api_key = settings.STRIPE_SECRET_KEY


def calculate_bag_total(bag):
    """Calculate the total amount for the items in the bag."""
    total = 0
    for item_id, quantity in bag.items():
        product = Product.objects.get(id=item_id)
        total += quantity * product.price
    return total


def checkout(request):
    if request.method == 'POST':
        bag = request.session.get('bag', {})
        order_form = OrderForm(request.POST)
        if not bag:
            messages.error(request, "Your bag is empty.")
            return redirect(reverse('products'))

        if order_form.is_valid():
            order = order_form.save(commit=False)
            pid = request.POST.get('stripe_pid', '').strip()
            
            # Calculate total again to ensure consistency
            stripe_total = round(calculate_bag_total(bag) * 100)  # Stripe requires amount in cents
            if stripe_total <= 0:
                messages.error(request, "Invalid bag total.")
                return redirect(reverse('view_bag'))
            
            try:
                intent = stripe.PaymentIntent.create(
                    amount=stripe_total,
                    currency=settings.STRIPE_CURRENCY,
                    metadata={'integration_check': 'accept_a_payment'}
                )
            except stripe.error.StripeError as e:
                messages.error(request, f"An error occurred: {e.user_message}")
                return redirect(reverse('checkout'))

            if pid:
                order.stripe_pid = pid
            else:
                order.stripe_pid = intent.id
            order.original_bag = json.dumps(bag)
            order.save()
            
            for item_id, quantity in bag.items():
                try:
                    product = Product.objects.get(id=item_id)
                    order_line_item = OrderLineItem(
                        order=order,
                        product=product,
                        quantity=quantity,
                    )
                    order_line_item.save()
                except Product.DoesNotExist:
                    messages.error(request, f"One of the products in your bag wasn't found in our database. \
                                    Please call us for assistance!")
                    order.delete()
                    return redirect(reverse('view_bag'))
            
            request.session['bag'] = {}  # Clear the bag in the session
            return redirect(reverse('checkout_success', args=[order.order_number]))
        else:
            messages.error(request, "There was an error with your form. Please check your information.")
    else:
        bag = request.session.get('bag', {})
        if not bag:
            messages.error(request, "Your bag is empty.")
            return redirect(reverse('products'))
        
        stripe_total = round(calculate_bag_total(bag) * 100)  # Stripe requires amount in cents
        if stripe_total > 0:
            try:
                intent = stripe.PaymentIntent.create(
                    amount=stripe_total,
                    currency=settings.STRIPE_CURRENCY,
                    metadata={'integration_check': 'accept_a_payment'}
                )
            except stripe.error.StripeError as e:
                messages.error(request, "Unable to create a payment intent. Please try again.")
                return redirect(reverse('checkout'))

            client_secret = intent.client_secret
        else:
            client_secret = None  # Handle cases where the total is 0 or bag is empty
        
        order_form = OrderForm()
        template = 'checkout/checkout.html'
        context = {
            'order_form': order_form,
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY,
            'client_secret': client_secret,
        }
        return render(request, template, context)


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
