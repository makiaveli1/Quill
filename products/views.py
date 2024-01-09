from django.db.models.functions import Lower
from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.db.models import Q
from django.contrib import messages
from .models import Product, Category, Author
from .forms import ProductForm, AuthorForm


def all_products(request):
    """A view to show all products,
    including sorting and search queries with pagination."""

    products_list = Product.objects.all()
    query = None
    categories = None
    authors = None
    sort = None
    direction = None

    if request.GET:
        if 'sort' in request.GET:
            sortkey = request.GET['sort']
            sort = sortkey
            if sortkey == 'name':
                sortkey = 'lower_name'
                products_list = products_list.annotate(
                    lower_name=Lower('name'))
            elif sortkey == 'category':
                sortkey = 'category__friendly_name'
            elif sortkey == 'author':
                sortkey = 'author__name'
            elif sortkey == 'price':
                sortkey = 'price'

            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}'
            products_list = products_list.order_by(sortkey)

        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products_list = products_list.filter(category__name__in=categories)
            categories = Category.objects.filter(name__in=categories)

        if 'author' in request.GET:
            authors = request.GET['author'].split(',')
            products_list = products_list.filter(author__name__in=authors)
            authors = Author.objects.filter(name__in=authors)

        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(
                    request, "You did not enter any search criteria!")
                return redirect(reverse('products'))

            queries = Q(name__icontains=query) | Q(
                description__icontains=query) | Q(
                author__name__icontains=query) | Q(
                    category__friendly_name__icontains=query)
            products_list = products_list.filter(queries)

    current_sorting = f"{sort}_{direction}"

    # Pagination setup
    paginator = Paginator(products_list, 10)  # Display 10 products per page
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    context = {
        'products': products,
        'search_term': query,
        'current_categories': categories,
        'current_authors': authors,
        'current_sorting': current_sorting,
    }

    return render(request, "products/products.html", context)


def product_detail(request, product_id):
    """A view to show a product's details"""

    product = get_object_or_404(Product, pk=product_id)
    author = product.author
    category = product.category

    context = {
        "product": product,
        "author": author,
        "category": category,
    }

    return render(request, "products/product_detail.html", context)


@login_required
def add_product(request):
    """
    View function to add a product.

    Only superusers can access this view. If the request method is POST,
    it validates the form data and saves the product. If the form is valid,
    it redirects to the product detail page. If the form is invalid, it
    displays an error message. If the request method is GET, it renders
    the add product form.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - If the request method is POST and the form is valid, it redirects
      to the product detail page.
    - If the request method is GET or the form is invalid, it renders the
      add product form.
    """
    if not request.user.is_superuser:
        messages.error(request, "Sorry, only store owners can do that.")
        return redirect(reverse("home"))

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(
                request, "Successfully added the product: " + product.name)
            return redirect(reverse("product_detail", args=[product.id]))
        else:
            messages.error(
                request, "Failed to add product. Please check the form is valid.")
    else:
        form = ProductForm()

    return render(request, "products/add_product.html", {"form": form})


@login_required
def add_author(request):
    """
    View function to add a new author.

    Only store owners (superusers) can access this view.
    If the request method is POST, the form data is validated and a new author is added.
    If the form is not valid, an error message is displayed.
    If the request method is GET, an empty form is displayed.

    Parameters:
    - request: The HTTP request object.

    Returns:
    - If the form is valid and a new author is added, redirects to the authors list view.
    - If the form is not valid, renders the add_author.html template with the form.
    - If the user is not a superuser, redirects to the home view with an error message.
    """
    if not request.user.is_superuser:
        messages.error(request, "Sorry, only store owners can do that.")
        return redirect(reverse("home"))

    if request.method == "POST":
        # Include request.FILES if your form handles image uploads
        form = AuthorForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Successfully added a new Author!")
            # Redirect to the authors list or another appropriate view
            return redirect(reverse("authors_list"))
        else:
            messages.error(
                request, "Failed to add a new Author. Please check the form is valid.")
    else:
        form = AuthorForm()

    return render(request, "products/add_author.html", {"form": form})


@login_required
def edit_product(request, product_id):
    """
    Edit a product.

    Args:
        request (HttpRequest): The HTTP request object.
        product_id (int): The ID of the product to be edited.

    Returns:
        HttpResponse: The HTTP response object.

    Raises:
        None
    """
    if not request.user.is_superuser:
        messages.error(request, "Sorry, only store owners can do that.")
        return redirect(reverse("home"))

    product = get_object_or_404(Product, pk=product_id)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"Successfully updated {product.name}!")
            return redirect(reverse("product_detail", args=[product.id]))
        else:
            messages.error(
                request, """Failed to update product.
                Please check the form is valid.""")
    else:
        form = ProductForm(instance=product)
        messages.info(request, f"You are editing {product.name}")

    return render(request, "products/edit_product.html", {"form": form,
                                                          "product": product})


@login_required
def delete_product(request, product_id):
    """Delete a Product from the store"""

    if not request.user.is_superuser:
        messages.error(request, "Sorry, only store owners can do that.")
        return redirect(reverse("home"))

    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, f"{product.name} deleted from the store")
    return redirect(reverse("products"))


def search_products(request):
    """A view to return the search results"""
    query = request.GET.get('q')

    if query:
        queries = Q(name__icontains=query) | Q(description__icontains=query) | Q(
            author__name__icontains=query) | Q(
                category__friendly_name__icontains=query)
        products = Product.objects.filter(queries)
    else:
        messages.error(request, "You didn't enter any search criteria!")
        products = Product.objects.none()

    context = {
        'products': products,
        'search_term': query,
    }

    return render(request, "products/search_results.html", context)
