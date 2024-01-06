from django.contrib import admin
from .models import Product, Category, Author


class CategoryAdmin(admin.ModelAdmin):
    """
    Display the Category model fields in the Admin view
    """
    list_display = ("name", "friendly_name", "slug")
    search_fields = ("name", "friendly_name")
    prepopulated_fields = {"slug": ("friendly_name",)}


class ProductAdmin(admin.ModelAdmin):
    """
    Display the Product model fields in the Admin view
    """
    list_display = (
        "name",
        "rating",
        "price",
        "category",
        "author",
        "format",
        "book_depository_stars",
        "currency",
        "old_price",
        "isbn",
        "slug",
        "image_url"
    )
    search_fields = ("name", "author__name", "category__name")
    list_filter = ("category", "author", "rating", "format")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("-rating",)


class AuthorAdmin(admin.ModelAdmin):
    """
    Display the Author model fields in the Admin view
    """
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Author, AuthorAdmin)
