from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import stripe
from checkout.webhook_handler import StripeWH_Handler
import logging

# Configure logging
logger = logging.getLogger(__name__)


@require_POST
@csrf_exempt
def webhook(request):
    """
    Listen for webhooks from Stripe.
    """

    # Set up Stripe API key and webhook secret to confirm the webhook came from Stripe
    wh_secret = settings.STRIPE_WH_SECRET
    stripe.api_key = settings.STRIPE_SECRET_KEY

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, wh_secret)
    except ValueError as e:
        # Invalid payload
        logger.error(
            "Invalid payload received from Stripe webhook.", exc_info=True)
        return HttpResponse(content="Invalid payload", status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error("Invalid signature for Stripe webhook.", exc_info=True)
        return HttpResponse(content="Invalid signature", status=400)
    except Exception as e:
        # Other unexpected exceptions
        logger.error("Error in Stripe webhook.", exc_info=True)
        return HttpResponse(content="Error in webhook", status=400)

    # Initialize the webhook handler
    handler = StripeWH_Handler(request)

    # Mapping of webhook events to relevant handler functions
    event_map = {
        'payment_intent.succeeded': handler.handle_payment_intent_succeeded,
        'payment_intent.payment_failed': handler.handle_payment_intent_payment_failed,
    }

    # Get the webhook type from Stripe
    event_type = event.get('type')

    # Get the appropriate handler function from the event_map, or use the generic handler by default
    event_handler = event_map.get(event_type, handler.handle_event)

    # Execute the handler function and return its response
    response = event_handler(event)
    logger.info(f"Handled webhook {event_type} successfully.")
    return response
