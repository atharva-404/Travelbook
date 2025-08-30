from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from decimal import Decimal
from datetime import date, time
from .models import TravelOption, Booking, UserProfile

class TravelOptionModelTest(TestCase):
    def setUp(self):
        self.travel = TravelOption.objects.create(
            travel_id='FL001',
            travel_type='flight',
            source='Mumbai',
            destination='Delhi',
            departure_date=date.today(),
            departure_time=time(10, 30),
            arrival_date=date.today(),
            arrival_time=time(12, 30),
            price=Decimal('5000.00'),
            total_seats=100,
        )

    def test_travel_option_creation(self):
        self.assertEqual(self.travel.travel_id, 'FL001')
        self.assertEqual(self.travel.available_seats, 100)
        self.assertEqual(str(self.travel), 'FL001 - Mumbai to Delhi')

class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.travel = TravelOption.objects.create(
            travel_id='FL001',
            travel_type='flight',
            source='Mumbai',
            destination='Delhi',
            departure_date=date.today(),
            departure_time=time(10, 30),
            arrival_date=date.today(),
            arrival_time=time(12, 30),
            price=Decimal('5000.00'),
            total_seats=100,
        )

    def test_booking_creation(self):
        booking = Booking.objects.create(
            user=self.user,
            travel_option=self.travel,
            number_of_seats=2,
            passenger_names=['John Doe', 'Jane Doe']
        )
        self.assertEqual(booking.number_of_seats, 2)
        self.assertEqual(booking.total_price, Decimal('10000.00'))
        self.assertEqual(booking.status, 'confirmed')
        self.assertTrue(booking.booking_id.startswith('BK'))

    def test_booking_cancellation(self):
        booking = Booking.objects.create(
            user=self.user,
            travel_option=self.travel,
            number_of_seats=2,
            passenger_names=['John Doe', 'Jane Doe']
        )
        initial_seats = self.travel.available_seats
        
        # Update seats after booking
        self.travel.available_seats -= booking.number_of_seats
        self.travel.save()
        
        # Cancel booking
        result = booking.cancel_booking()
        self.assertTrue(result)
        self.assertEqual(booking.status, 'cancelled')
        
        # Refresh travel option
        self.travel.refresh_from_db()
        self.assertEqual(self.travel.available_seats, initial_seats)

class ViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.travel = TravelOption.objects.create(
            travel_id='FL001',
            travel_type='flight',
            source='Mumbai',
            destination='Delhi',
            departure_date=date.today(),
            departure_time=time(10, 30),
            arrival_date=date.today(),
            arrival_time=time(12, 30),
            price=Decimal('5000.00'),
            total_seats=100,
        )

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'TravelBook')

    def test_travel_list_view(self):
        response = self.client.get(reverse('travel_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FL001')

    def test_booking_requires_login(self):
        response = self.client.get(reverse('book_travel', args=[self.travel.id]))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_booking_with_login(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('book_travel', args=[self.travel.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Book Your Travel')

    def test_user_registration(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'testpass123456',
            'password2': 'testpass123456',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertTrue(User.objects.filter(username='newuser').exists())

class FormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.travel = TravelOption.objects.create(
            travel_id='FL001',
            travel_type='flight',
            source='Mumbai',
            destination='Delhi',
            departure_date=date.today(),
            departure_time=time(10, 30),
            arrival_date=date.today(),
            arrival_time=time(12, 30),
            price=Decimal('5000.00'),
            total_seats=100,
        )

    def test_booking_form_validation(self):
        from .forms import BookingForm
        
        # Test valid form
        form = BookingForm(data={
            'number_of_seats': 2,
            'passenger_names': 'John Doe\nJane Doe'
        }, travel_option=self.travel)
        self.assertTrue(form.is_valid())
        
        # Test invalid form - too many seats
        form = BookingForm(data={
            'number_of_seats': 150,
            'passenger_names': 'John Doe'
        }, travel_option=self.travel)
        self.assertFalse(form.is_valid())
        
        # Test invalid form - mismatched passenger names
        form = BookingForm(data={
            'number_of_seats': 2,
            'passenger_names': 'John Doe'  # Only one name for 2 seats
        }, travel_option=self.travel)
        self.assertFalse(form.is_valid())