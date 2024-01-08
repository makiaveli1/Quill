from django import forms
from .widgets import CustomClearableFileInput
from .models import Product, Author, Category


class ProductForm(forms.ModelForm):
    """
    Store Owner/Admin Product Form to manage Store's product offering
    """

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'rating', 'category',
                  'author',
                  'format', 'book_depository_stars', 'currency', 'old_price',
                  'isbn', 'image_url']
        labels = {
            'isbn': 'ISBN',
            'image_url': 'Image URL'
        }

    image_url = forms.URLField(
        label="Image URL", required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = Category.objects.all()
        friendly_names = [(c.id, c.get_friendly_name()) for c in categories]
        self.fields['category'].choices = friendly_names
        authors = Author.objects.all()
        author_names = [(a.id, a.name) for a in authors]
        self.fields['author'].choices = author_names


class AuthorForm(forms.ModelForm):
    """
    Form for admin to add or update authors
    """

    class Meta:
        model = Author
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
