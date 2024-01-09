from django.shortcuts import render, get_object_or_404, redirect
from .models import Profile
from django.contrib.auth.decorators import login_required
from .forms import ProfileForm  # Ensure this form is appropriately set up
from django.contrib import messages
from products.models import Product  # Import Product model


@login_required
def profile(request):
    """
    Display and edit the user's profile, including managing their wishlist.
    """
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('profile')  # Redirect to avoid POST on reload
        else:
            messages.error(
                request, 'Update failed. Please ensure the form is valid.')
    else:
        form = ProfileForm(instance=profile)

    wishlist_products = profile.wishlist.all()

    template = 'profiles/profile.html'
    context = {
        'form': form,
        'wishlist_products': wishlist_products,
        'on_profile_page': True,
    }

    return render(request, template, context)


@login_required
def order_history(request, order_number):
    """
    Display a user's order history
    """
    order = get_object_or_404(Order, order_number=order_number,
                              user=request.user)  # Ensure user has access to this order

    messages.info(request, (
        f'This is a past confirmation for order number {order_number}. '
        'A confirmation email was sent on the order date.'
    ))

    template = 'orders/order_history.html'  # Adjust if using a different template
    context = {
        'order': order,
        'from_profile': True,  # Differentiate access from direct purchase
    }

    return render(request, template, context)
