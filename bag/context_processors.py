"""_summary_
"""


def bag_contents(request):
    """
    Retrieve the bag contents from the session and calculate the total number of items.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        dict: A dictionary containing the total number of items in the bag.
    """
    bag = request.session.get('bag', {})
    total_items = sum(bag.values())

    return {'total_items': total_items}
