from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_resized import ResizedImageField


class Profile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    image = ResizedImageField(
        size=[300, 300], quality=75, upload_to='profiles/',
        force_format='WEBP', blank=True)
    bio = models.TextField(max_length=2500, null=True, blank=True)
    # New field for favorite book genre
    favorite_genre = models.CharField(max_length=100, blank=True)
    wishlist = models.ManyToManyField('products.Product', blank=True)
    default_phone_number = models.CharField(
        max_length=20, null=True, blank=True)
    default_country = CountryField(
        blank_label='Country *', null=True, blank=True)
    default_post_code = models.CharField(max_length=20, null=True, blank=True)
    default_town_or_city = models.CharField(
        max_length=60, null=True, blank=True)
    default_address_line1 = models.CharField(
        max_length=80, null=True, blank=True)
    default_address_line2 = models.CharField(
        max_length=80, null=True, blank=True)
    default_county_or_state = models.CharField(
        max_length=80, null=True, blank=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
