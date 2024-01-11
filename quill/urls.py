"""quill URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse


def robots_txt(request):
    """
    View function for generating the robots.txt file.

    This function returns a HttpResponse object with the content of the robots.txt file.
    The robots.txt file contains instructions for web robots (also known as web crawlers) on how to crawl and index a website.

    :param request: The HTTP request object.
    :return: A HttpResponse object with the content of the robots.txt file.
    """
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Sitemap: https://www.yourdomain.com/sitemap.xml"
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


urlpatterns = [
    path('admin/', admin.site.urls),
    path("robots.txt", robots_txt),
    path('accounts/', include('allauth.urls')),
    path('', include('home.urls')),
    path('products/', include('products.urls')),
    path('profile/', include('profiles.urls')),
    path('bag/', include('bag.urls')),
    path('checkout/', include('checkout.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
