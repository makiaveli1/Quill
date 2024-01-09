from django.shortcuts import render, redirect, reverse, HttpResponse, get_object_or_404
from products.models import Product
from django.contrib import messages


def view_bag(request):
    """
    A view to return and display the shopping bag.
    """
    bag = request.session.get('bag', {})
    total_items = sum(bag.values())
    bag_items = []
    total = 0

    # Iterate over the bag items and calculate the total cost
    for item_id, quantity in bag.items():
        product = get_object_or_404(Product, pk=item_id)
        total += quantity * product.price
        bag_items.append({
            'item_id': item_id,
            'quantity': quantity,
            'product': product,
            'subtotal': quantity * product.price,
        })

    context = {
        'bag_items': bag_items,
        'total': total,
        'total_items': total_items,
    }

    return render(request, "bag/bag.html", context)


def add_to_bag(request, item_id):
    """
    Add a product to the shopping bag.

    Args:
        request (HttpRequest): The HTTP request object.
        item_id (int): The ID of the product to be added.

    Returns:
        HttpResponseRedirect: Redirects to the specified URL after adding the product to the bag.
    """
    product = get_object_or_404(Product, pk=item_id)
    quantity = int(request.POST.get('quantity', 1))
    redirect_url = request.POST.get('redirect_url', reverse('products'))

    bag = request.session.get('bag', {})

    if item_id in bag:
        bag[item_id] += quantity
    else:
        bag[item_id] = quantity

    request.session['bag'] = bag
    messages.success(request, f"Added {product.name} to your bag.")
    return redirect(redirect_url)


def adjust_bag(request, item_id):
    """
    Adjust the quantity of the specified product in the shopping bag.
    """
    product = get_object_or_404(Product, pk=item_id)
    quantity = int(request.POST.get("quantity"))
    bag = request.session.get("bag", {})

    if quantity > 0:
        bag[item_id] = quantity
        messages.success(request, f"""Updated {
                         product.name} quantity to {bag[item_id]}.""")
    else:
        bag.pop(item_id, None)
        messages.success(request, f"Removed {product.name} from your bag.")

    request.session["bag"] = bag
    return redirect(reverse("view_bag"))


def delete_from_bag(request, item_id):
    """
    Delete a product from the shopping bag.
    """
    try:
        product = get_object_or_404(Product, pk=item_id)
        bag = request.session.get("bag", {})

        bag.pop(item_id, None)
        messages.success(request, f"Removed {product.name} from your bag.")
        request.session["bag"] = bag

        # Redirect back to the shopping cart page
        return redirect(reverse('view_bag'))
    except Exception as e:
        messages.error(request, f"Error removing item: {e}.")
        # Redirect back to the shopping cart page in case of error
        return redirect(reverse('view_bag'))
