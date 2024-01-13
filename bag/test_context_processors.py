from django.test import RequestFactory, TestCase
from .context_processors import bag_contents

class BagContentsTestCase(TestCase):
    def test_bag_contents_with_empty_bag(self):
        # Create a request object
        request = RequestFactory().get('/')
        request.session = {}

        # Call the bag_contents function
        result = bag_contents(request)

        # Check if the result is as expected
        self.assertEqual(result, {'total_items': 0})

    def test_bag_contents_with_non_empty_bag(self):
        # Create a request object
        request = RequestFactory().get('/')
        request.session = {'bag': {'item1': 2, 'item2': 3}}

        # Call the bag_contents function
        result = bag_contents(request)

        # Check if the result is as expected
        self.assertEqual(result, {'total_items': 5})