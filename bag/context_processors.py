from django.shortcuts import get_object_or_404
# Import your Product and Category models
from products.models import Product, Category


def bag_contents(request):
    """
    Context processor to include bag contents and total cost in the context for all templates.
    """
    bag_items = []
    total = 0
    product_count = 0
    bag = request.session.get('bag', {})

    for item_id, quantity in bag.items():
        product = get_object_or_404(Product, pk=item_id)
        total += quantity * product.price
        product_count += quantity
        bag_items.append({
            'item_id': item_id,
            'quantity': quantity,
            'product': product,
            'subtotal': quantity * product.price,
        })

    grand_total = total  # Since there are no delivery costs for eBooks

    return {
        'bag_items': bag_items,
        'total': total,
        'product_count': product_count,
        'grand_total': grand_total,
    }


def categories_processor(request):
    return {'categories': Category.objects.all()}
