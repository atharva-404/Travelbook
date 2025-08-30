from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Booking, UserProfile
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Div, Field
import json

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Register', css_class='btn btn-primary'))

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Update Profile', css_class='btn btn-primary'))

class BookingForm(forms.ModelForm):
    passenger_names = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter passenger names (one per line)'}),
        help_text='Enter one passenger name per line'
    )

    class Meta:
        model = Booking
        fields = ['number_of_seats', 'passenger_names']

    def __init__(self, *args, **kwargs):
        self.travel_option = kwargs.pop('travel_option', None)
        super().__init__(*args, **kwargs)
        
        if self.travel_option:
            self.fields['number_of_seats'].widget.attrs.update({
                'max': self.travel_option.available_seats,
                'min': 1
            })
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Confirm Booking', css_class='btn btn-success'))

    def clean_number_of_seats(self):
        seats = self.cleaned_data['number_of_seats']
        if self.travel_option and seats > self.travel_option.available_seats:
            raise forms.ValidationError(f"Only {self.travel_option.available_seats} seats available.")
        return seats

    def clean_passenger_names(self):
        names_text = self.cleaned_data['passenger_names']
        names = [name.strip() for name in names_text.split('\n') if name.strip()]
        
        number_of_seats = self.cleaned_data.get('number_of_seats', 0)
        if len(names) != number_of_seats:
            raise forms.ValidationError(f"Please provide exactly {number_of_seats} passenger names.")
        
        return names

class TravelSearchForm(forms.Form):
    TRAVEL_TYPES = [
        ('', 'All Types'),
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('bus', 'Bus'),
    ]
    
    travel_type = forms.ChoiceField(choices=TRAVEL_TYPES, required=False)
    source = forms.CharField(max_length=100, required=False)
    destination = forms.CharField(max_length=100, required=False)
    departure_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.add_input(Submit('submit', 'Search', css_class='btn btn-primary'))