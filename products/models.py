from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class ProductManager(models.Manager):
    """
    Custom Model Manager for the Product model.
    """

    def get_by_category(self, category_name):
        """
        Returns all products in a given category.
        """
        return self.get_queryset().filter(category__name=category_name)

    def get_by_author(self, author_name):
        """
        Returns all products by a given author.
        """
        return self.get_queryset().filter(author__name=author_name)


class Author(models.Model):
    """
    Model representing an author.
    """
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        """
        Metadata for the Author model.
        """
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'
        ordering = ['name']

    def save(self, *args, **kwargs):
        """
        Save method for Author. Generates a slug if one isn't provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Model representing a category.
    """
    name = models.CharField(max_length=100, db_index=True)
    friendly_name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        """
        Metadata for the Category model.
        """
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['friendly_name']

    def save(self, *args, **kwargs):
        """
        Save method for Category. Generates a slug if one isn't provided.
        """
        if not self.slug:
            self.slug = slugify(self.friendly_name)
        super().save(*args, **kwargs)

    def get_friendly_name(self):
        """
        Returns the friendly name of the category.
        """
        return self.friendly_name

    def __str__(self):
        return self.friendly_name


class Product(models.Model):
    """
    Model representing a product.
    """
    sku = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products')
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    image_url = models.URLField()  # URL from AWS
    author = models.ForeignKey(
        Author, on_delete=models.CASCADE, related_name='products')
    format = models.CharField(max_length=100)
    book_depository_stars = models.DecimalField(max_digits=2, decimal_places=1)
    currency = models.CharField(max_length=10)
    old_price = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True)
    isbn = models.BigIntegerField()
    slug = models.SlugField(unique=True, blank=True)

    objects = ProductManager()  # Custom model manager

    class Meta:
        """
        Metadata for the Product model.
        """
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']

    def save(self, *args, **kwargs):
        """
        Save method for Product. Generates a slug if one isn't provided.
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        """
        Validation for Product. Ensures price and old_price are not negative.
        """
        if self.price and self.price < 0:
            raise ValidationError('Price cannot be negative.')
        if self.old_price and self.old_price < 0:
            raise ValidationError('Old price cannot be negative.')

    def __str__(self):
        return self.name
