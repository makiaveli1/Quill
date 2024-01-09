from django import template

register = template.Library()


@register.filter(name="calc_subtotal")
def calc_subtotal(price, quantity):
    """
    Calculates the subtotal by multiplying the price and quantity.

    Args:
        price (float): The price of the item.
        quantity (int): The quantity of the item.

    Returns:
        float: The subtotal of the item.
    """
    return price * quantity
