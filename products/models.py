from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify

# Custom Model Manager


class ProductManager(models.Manager):
    def get_by_category(self, category_name):
        return self.get_queryset().filter(category__name=category_name)

    def get_by_author(self, author_name):
        return self.get_queryset().filter(author__name=author_name)

# Author Model


class Author(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Author, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

# Category Model


class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True)
    friendly_name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['friendly_name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.friendly_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.friendly_name

# Product Model


class Product(models.Model):
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
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    def clean(self):
        if self.price and self.price < 0:
            raise ValidationError('Price cannot be negative.')
        if self.old_price and self.old_price < 0:
            raise ValidationError('Old price cannot be negative.')

    def __str__(self):
        return self.name
