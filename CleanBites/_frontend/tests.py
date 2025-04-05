from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.messages import get_messages

from _api._users.models import Customer, DM
from _api._restaurants.models import Restaurant
from _frontend.utils import (
    has_unread_messages
)
from django.contrib.gis.geos import Point

User = get_user_model()


class ViewTests(TestCase):
    def setUp(self):
        # Create test user
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="testpass123"
        )
        self.customer1 = Customer.objects.create(
            username="user1", email="user1@test.com", first_name="User", last_name="One"
        )

        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="testpass123"
        )
        self.customer2 = Customer.objects.create(
            username="user2", email="user2@test.com", first_name="User", last_name="Two"
        )

        self.client = Client()

    def test_landing_view(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")

    def test_home_view_authenticated(self):
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_home_view_unauthenticated(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("login")))

    def test_register_view_post_valid(self):
        data = {
            "username": "newuser",
            "email": "new@test.com",
            "password1": "complexpassword123",
            "password2": "complexpassword123",
        }
        response = self.client.post(reverse("register"), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_profile_router(self):
        # Create restaurant user and associated restaurant
        restaurant_user = User.objects.create_user(
            username="restaurant1",
            password="testpass123",
            email="restaurant@test.com",
        )

        # Create the restaurant record with matching username
        restaurant = Restaurant.objects.create(
            username="restaurant1",
            name="Test Restaurant",
            email="restaurant@test.com",
            phone="123-456-7890",
            building=123,
            street="Test St",
            zipcode="10001",
            borough=1,
            cuisine_description="American",
            hygiene_rating=1,
            violation_description="No violations",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.966, 40.78),
        )

        # Login as restaurant
        self.client.login(username="restaurant1", password="testpass123")

        # Test profile router redirect
        response = self.client.get(reverse("user_profile", args=[restaurant.username]))

        # Verify the redirected page loads correctly
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["restaurant"], restaurant)

    def test_messages_view(self):
        """Test messages_view functionality"""
        # Test with no messages
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("messages inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["conversations"]), 0)
        self.assertIsNone(response.context["active_chat"])
        self.assertEqual(len(response.context["messages"]), 0)

        # Create test messages
        DM.objects.create(
            sender=self.customer1,
            receiver=self.customer2,
            message=b"Test message 1",
        )
        DM.objects.create(
            sender=self.customer2,
            receiver=self.customer1,
            message=b"Test message 2",
            read=False,
        )

        # Test conversation list
        response = self.client.get(reverse("messages inbox"))
        self.assertEqual(len(response.context["conversations"]), 1)
        self.assertEqual(response.context["conversations"][0]["id"], self.customer2.id)
        self.assertTrue(response.context["conversations"][0]["has_unread"])

        # Test message decoding
        chat_response = self.client.get(
            reverse("chat", kwargs={"chat_user_id": self.customer2.id})
        )
        self.assertEqual(len(chat_response.context["messages"]), 2)
        self.assertEqual(
            chat_response.context["messages"][0].decoded_message, "Test message 1"
        )
        self.assertEqual(
            chat_response.context["messages"][1].decoded_message, "Test message 2"
        )

        # Verify unread message was marked as read
        updated_dm = DM.objects.get(message=b"Test message 2")
        self.assertTrue(updated_dm.read)

        # Test error handling for missing profile
        self.customer1.delete()
        error_response = self.client.get(reverse("messages inbox"))
        self.assertEqual(len(error_response.context["conversations"]), 0)
        self.assertEqual(
            error_response.context["error"], "Your profile could not be found."
        )

    def test_dynamic_map_view(self):
        """Test dynamic_map_view returns 200 and correct context"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("dynamic-map"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("has_unread_messages", response.context)
        self.assertTemplateUsed(response, "maps/nycmap_dynamic.html")


class MessageSystemTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="testpass123"
        )
        self.customer1 = Customer.objects.create(
            username="user1", email="user1@test.com", first_name="User", last_name="One"
        )

        self.user2 = User.objects.create_user(
            username="user2", email="user2@test.com", password="testpass123"
        )
        self.customer2 = Customer.objects.create(
            username="user2", email="user2@test.com", first_name="User", last_name="Two"
        )

        self.client = Client()

    def test_dm_creation(self):
        """Test basic DM creation"""
        dm = DM.objects.create(
            sender=self.customer1,
            receiver=self.customer2,
            message=b"Test message",
            read=False,
        )
        self.assertEqual(dm.sender, self.customer1)
        self.assertEqual(dm.receiver, self.customer2)
        self.assertEqual(dm.message, b"Test message")
        self.assertFalse(dm.read)
        self.assertFalse(dm.flagged)
        self.assertIsNone(dm.flagged_by)

    def test_dm_self_send_prevention(self):
        """Test that users can't send DMs to themselves"""
        with self.assertRaises(ValidationError):
            dm = DM(
                sender=self.customer1, receiver=self.customer1, message=b"Test message"
            )
            dm.full_clean()

    def test_has_unread_messages(self):
        """Test the has_unread_messages utility function"""
        # No messages initially
        self.assertFalse(has_unread_messages(self.user1))

        # Create unread message
        DM.objects.create(
            sender=self.customer2,
            receiver=self.customer1,
            message=b"Test message",
            read=False,
        )
        self.assertTrue(has_unread_messages(self.user1))

        # Mark as read
        DM.objects.filter(receiver=self.customer1).update(read=True)
        self.assertFalse(has_unread_messages(self.user1))

    def test_message_view_mark_read(self):
        """Test that viewing messages marks them as read"""
        # Create unread message
        DM.objects.create(
            sender=self.customer2,
            receiver=self.customer1,
            message=b"Test message",
            read=False,
        )

        # Login and view messages
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("messages inbox"))

        # Message should now be marked as read
        self.assertFalse(
            DM.objects.filter(receiver=self.customer1, read=False).exists()
        )

    def test_delete_conversation(self):
        """Test that conversation deletion works correctly"""
        # Create test messages between users
        DM.objects.create(
            sender=self.customer1,
            receiver=self.customer2,
            message=b"Message 1",
        )
        DM.objects.create(
            sender=self.customer2,
            receiver=self.customer1,
            message=b"Message 2",
        )

        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("delete_conversation", kwargs={"other_user_id": self.customer2.id})
        )

        # Verify redirect
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("messages inbox"))

        # Verify messages were deleted
        self.assertEqual(DM.objects.count(), 0)

        # Verify success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn(
            f"Conversation with {self.customer2.first_name}", str(messages[0])
        )


class UtilityTests(TestCase):
    """Basic tests for utility functions"""

    def setUp(self):
        # Create two test users
        self.user1 = User.objects.create_user(
            username="test1", email="test1@test.com", password="testpass123"
        )
        self.customer1 = Customer.objects.create(
            username="test1", email="test1@test.com"
        )

        self.user2 = User.objects.create_user(
            username="test2", email="test2@test.com", password="testpass123"
        )
        self.customer2 = Customer.objects.create(
            username="test2", email="test2@test.com"
        )

        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            username="restaurant1",
            email="restaurant@test.com",
            borough=1,  # Manhattan is typically represented as 1
            building=123,
            street="Test St",
            zipcode="10001",
            phone="123-456-7890",
            cuisine_description="American",
            hygiene_rating=1,
            violation_description="No violations",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.966, 40.78),  # Example NYC coordinates
        )

    def test_has_unread_messages_utility(self):
        """Test has_unread_messages returns correct boolean"""
        # No messages
        self.assertFalse(has_unread_messages(self.user1))

        # User2 sends message to User1
        DM.objects.create(
            sender=self.customer2, receiver=self.customer1, message=b"test", read=False
        )
        self.assertTrue(has_unread_messages(self.user1))
        self.assertFalse(has_unread_messages(self.user2))


class RestaurantViewTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="user1", email="user1@test.com", password="testpass123"
        )
        self.customer1 = Customer.objects.create(
            username="user1", email="user1@test.com", first_name="User", last_name="One"
        )

        # Create test restaurant
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            username="restaurant1",
            email="restaurant@test.com",
            borough=1,  # Manhattan is typically represented as 1
            building=123,
            street="Test St",
            zipcode="10001",
            phone="123-456-7890",
            cuisine_description="American",
            hygiene_rating=1,
            violation_description="No violations",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.966, 40.78),  # Example NYC coordinates
        )

        self.client = Client()

    def test_restaurant_detail_view(self):
        """Test restaurant detail view for both owners and regular users"""
        # Test as non-owner
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.name])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_owner"])
        self.assertEqual(response.context["restaurant"], self.restaurant)

        # Test as owner
        owner = User.objects.create_user(
            username="restaurant1", email="restaurant@test.com", password="testpass123"
        )
        self.client.login(username="restaurant1", password="testpass123")
        response = self.client.get(
            reverse("restaurant_detail", args=[self.restaurant.name])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_owner"])

    def test_restaurant_detail_case_insensitive(self):
        """Test restaurant name matching is case insensitive"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(
            reverse("restaurant_detail", args=["test restaurant"])
        )
        self.assertEqual(response.status_code, 200)

    def test_restaurant_register_view(self):
        """Test restaurant registration page shows unverified restaurants"""
        # Create unverified restaurant
        Restaurant.objects.create(
            name="Unverified Restaurant",
            email="Not Provided",
            phone="123-456-7890",
            building=123,
            street="Test St",
            zipcode="10001",
            borough=1,  # Manhattan
            cuisine_description="American",
            hygiene_rating=1,
            violation_description="No violations",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.966, 40.78),  # NYC coordinates
        )

        response = self.client.get(reverse("restaurant_register"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["restaurants"]), 1)

    def test_restaurant_verify_success(self):
        """Test successful restaurant verification"""
        restaurant = Restaurant.objects.create(
            name="Unverified Restaurant",
            email="Not Provided",
            phone="123-456-7890",
            building=123,
            street="Test St",
            zipcode="10001",
            borough=1,  # Manhattan
            cuisine_description="American",
            hygiene_rating=1,
            violation_description="No violations",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.966, 40.78),  # NYC coordinates
        )

        data = {
            "restaurant": restaurant.id,
            "username": "newowner",
            "email": "owner@test.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "verify": "1234",
        }

        response = self.client.post(reverse("restaurant_verify"), data)
        self.assertEqual(response.status_code, 302)

        # Verify updates
        updated = Restaurant.objects.get(id=restaurant.id)
        self.assertEqual(updated.email, "owner@test.com")
        self.assertEqual(updated.username, "newowner")
        self.assertTrue(User.objects.filter(username="newowner").exists())

    def test_restaurant_verify_failures(self):
        """Test various failure cases for restaurant verification"""
        restaurant = Restaurant.objects.create(
            name="Unverified Restaurant",
            email="test@example.com",
            phone="123-456-7890",
            building=123,
            street="Test St",
            zipcode="10001",
            borough=1,  # Manhattan
            cuisine_description="American",
            hygiene_rating=1,
            violation_description="No violations",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.966, 40.78),  # NYC coordinates
        )

        # Test wrong verification code
        data = {
            "restaurant": restaurant.id,
            "username": "newowner",
            "email": "owner@test.com",
            "password": "testpass123",
            "confirm_password": "testpass123",
            "verify": "wrongcode",
        }
        response = self.client.post(reverse("restaurant_verify"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Restaurant.objects.get(id=restaurant.id).email, "test@example.com"
        )

        # Test password mismatch
        data = {
            "restaurant": restaurant.id,
            "username": "newowner",
            "email": "owner@test.com",
            "password": "testpass123",
            "confirm_password": "mismatch",
            "verify": "1234",
        }
        response = self.client.post(reverse("restaurant_verify"), data)
        self.assertEqual(response.status_code, 302)
