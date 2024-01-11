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
    stripe_public_key = settings.STRIPE_PUBLIC_KEY
    stripe_secret_key = settings.STRIPE_SECRET_KEY

    if request.method == 'POST':
        bag = request.session.get('bag', {})
        form_data = {
            'full_name': request.POST['full_name'],
            'email': request.POST['email'],
            'phone_number': request.POST['phone_number'],
            'country': request.POST['country'],
            'post_code': request.POST['post_code'],
            'town_or_city': request.POST['town_or_city'],
            'address_line1': request.POST['address_line1'],
            'address_line2': request.POST['address_line2'],
            'county_or_state': request.POST['county_or_state'],
        }
        order_form = OrderForm(form_data)

        if order_form.is_valid():
            try:
                with transaction.atomic():
                    order = order_form.save(commit=False)
                    client_secret = request.POST.get('client_secret')
                    logger.debug(f'Received client_secret: {request.POST.get("client_secret")}')
                    logger.debug(f'Received bag: {bag}')

                    if client_secret:
                        pid = client_secret.split('_secret')[0]
                        order.stripe_pid = pid
                        order.original_bag = json.dumps(bag)
                        order.save()
                        logger.debug(f'Order {order.id} saved with PID: {pid}')

                        payment_intent_id = request.POST.get(
                            'payment_intent_id', '')
                        if payment_intent_id and payment_intent_id == order.stripe_pid:
                            order.payment_status = 'Completed'
                            order.save()
                            logger.debug(f'Order {order.id} payment completed')
                            logger.debug(f'Received payment_intent_id: {payment_intent_id}')
                            logger.debug(f'Expected Stripe PID: {order.stripe_pid}')

                            # Process each item in the bag
                            for item_id, quantity in bag.items():
                                product = Product.objects.get(id=item_id)
                                order_line_item = OrderLineItem(
                                    order=order,
                                    product=product,
                                    quantity=quantity
                                )
                                order_line_item.save()

                            request.session['save_info'] = 'save_info' in request.POST
                            return redirect(reverse('checkout_success', args=[order.order_number]))
                        else:
                            logger.error(f'''Payment ID mismatch for order {order.id}, expected {
                                         order.stripe_pid}, got {payment_intent_id}''')
                            messages.error(request, "Payment ID mismatch.")
                            return redirect(reverse('view_bag'))
                    else:
                        logger.error(
                            'Client secret not provided for the payment.')
                        messages.error(request, "Invalid payment information.")
                        return redirect(reverse('view_bag'))

            except Exception as e:
                logger.error(f'Error processing checkout: {e}')
                messages.error(
                    request, "An error occurred while processing your order.")
                return redirect(reverse('view_bag'))
        else:
            logger.error(f'Invalid order form data: {order_form.errors}')
            messages.error(
                request, "There was an error with your form. Please double check your information.")
            return render(request, 'checkout/checkout.html', {'order_form': order_form})
    else:
        # Handling GET request
        bag = request.session.get('bag', {})
        if not bag:
            messages.error(request, "Your bag is empty.")
            return redirect(reverse('products'))

        current_bag = bag_contents(request)
        total = current_bag.get('grand_total', 0)
        stripe_total = round(total * 100)

        if stripe_total <= 0:
            messages.error(
                request, "There is an error with the total amount. Please check your bag.")
            return redirect(reverse('view_bag'))

        stripe.api_key = stripe_secret_key
        intent = stripe.PaymentIntent.create(
            amount=stripe_total,
            currency=settings.STRIPE_CURRENCY
        )

        # Handling user profile data for authenticated users
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
                logger.info(f'''Profile for user {
                            request.user.username} does not exist.''')

    context = {
        'order_form': order_form,
        'stripe_client_secret': intent.client_secret if stripe_total > 0 else None,
        'client_secret': intent.client_secret if stripe_total > 0 else None,
        'total_items': len(bag),
        'stripe_public_key': stripe_public_key,
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
