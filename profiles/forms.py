from django import forms
from .models import Profile
from django_countries.widgets import CountrySelectWidget


class ProfileForm(forms.ModelForm):
    """
    A form to render the Profile fields.
    """

    class Meta:
        model = Profile
        fields = [
            'image', 'bio', 'favorite_genre', 'default_phone_number',
            'default_country', 'default_post_code', 'default_town_or_city',
            'default_address_line1', 'default_address_line2',
            'default_county_or_state'
        ]
        widgets = {
            'default_country': CountrySelectWidget()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        placeholders = {
            'image': 'Profile Image',
            'bio': 'Bio',
            'favorite_genre': 'Favorite Book Genre',
            'default_phone_number': 'Phone Number',
            'default_country': 'Country',
            'default_post_code': 'Postal Code',
            'default_town_or_city': 'Town or City',
            'default_address_line1': 'Address Line 1',
            'default_address_line2': 'Address Line 2',
            'default_county_or_state': 'County, State or Locality',
        }

        self.fields['default_address_line1'].widget.attrs['autofocus'] = True
        for field in self.fields:
            if self.fields[field].required:
                placeholder = f'{placeholders[field]} *'
            else:
                placeholder = placeholders[field]
            self.fields[field].widget.attrs['placeholder'] = placeholder
            self.fields[field].widget.attrs['class'] = '''border-black
            rounded-0 profile-form-input'''
            self.fields[field].label = False

        # Special handling for CountryField to show a dropdown
        if 'default_country' in self.fields:
            self.fields['default_country'].widget.attrs['class'] = '''
            custom-select border-black rounded-0'''
