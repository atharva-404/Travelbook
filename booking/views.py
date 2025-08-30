from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import transaction
from .models import TravelOption, Booking, UserProfile
from .forms import CustomUserCreationForm, BookingForm, TravelSearchForm, UserProfileForm

def home(request):
    recent_travels = TravelOption.objects.filter(available_seats__gt=0)[:6]
    return render(request, 'booking/home.html', {'recent_travels': recent_travels})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def travel_list(request):
    form = TravelSearchForm(request.GET)
    travels = TravelOption.objects.filter(available_seats__gt=0)
    
    if form.is_valid():
        if form.cleaned_data['travel_type']:
            travels = travels.filter(travel_type=form.cleaned_data['travel_type'])
        if form.cleaned_data['source']:
            travels = travels.filter(source__icontains=form.cleaned_data['source'])
        if form.cleaned_data['destination']:
            travels = travels.filter(destination__icontains=form.cleaned_data['destination'])
        if form.cleaned_data['departure_date']:
            travels = travels.filter(departure_date=form.cleaned_data['departure_date'])
    
    paginator = Paginator(travels, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'booking/travel_list.html', {
        'form': form,
        'page_obj': page_obj,
        'travels': page_obj.object_list
    })

@login_required
def book_travel(request, travel_id):
    travel = get_object_or_404(TravelOption, id=travel_id, available_seats__gt=0)
    
    if request.method == 'POST':
        form = BookingForm(request.POST, travel_option=travel)
        if form.is_valid():
            with transaction.atomic():
                booking = form.save(commit=False)
                booking.user = request.user
                booking.travel_option = travel
                booking.total_price = travel.price * booking.number_of_seats
                booking.save()
                
                # Update available seats
                travel.available_seats -= booking.number_of_seats
                travel.save()
                
                messages.success(request, f'Booking confirmed! Your booking ID is {booking.booking_id}')
                return redirect('my_bookings')
    else:
        form = BookingForm(travel_option=travel)
    
    return render(request, 'booking/book_travel.html', {
        'travel': travel,
        'form': form
    })

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user)
    return render(request, 'booking/my_bookings.html', {'bookings': bookings})

@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    
    if booking.cancel_booking():
        messages.success(request, 'Booking cancelled successfully!')
    else:
        messages.error(request, 'Unable to cancel this booking.')
    
    return redirect('my_bookings')

@login_required
def profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'booking/profile.html', {'form': form})