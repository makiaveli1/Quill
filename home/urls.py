from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .import views

urlpatterns = [
    path('', views.index, name='home'),
    path('admin/', admin.site.urls ),
    path('about_us', views.about_us, name='about_us'),
    path('privacy_policy', views.privacy_policy, name='privacy_policy'),
    
]
