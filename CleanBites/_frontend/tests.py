from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.messages import get_messages

from _api._users.models import Customer, DM, FavoriteRestaurant
from _api._restaurants.models import Restaurant
from _frontend.utils import has_unread_messages
from django.contrib.gis.geos import Point
from django.test import RequestFactory

User = get_user_model()


# ALL FRONTEND TESTS ==================================================================
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

    def test_active_chat_selection(self):
        """Test active chat selection logic in messages_view"""
        # Create test messages
        DM.objects.create(
            sender=self.customer1,
            receiver=self.customer2,
            message=b"First message",
        )
        DM.objects.create(
            sender=self.customer2,
            receiver=self.customer1,
            message=b"Second message",
        )

        # Test 1: No chat_user_id specified - should default to first conversation
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(reverse("messages inbox"))
        self.assertEqual(response.context["active_chat"].id, self.customer2.id)
        self.assertEqual(len(response.context["messages"]), 2)
        self.assertEqual(
            response.context["messages"][0].decoded_message, "First message"
        )
        self.assertEqual(
            response.context["messages"][1].decoded_message, "Second message"
        )

        # Test 2: Specific chat_user_id specified
        response = self.client.get(
            reverse("chat", kwargs={"chat_user_id": self.customer2.id})
        )
        self.assertEqual(response.context["active_chat"].id, self.customer2.id)
        self.assertEqual(len(response.context["messages"]), 2)

        # Test 3: Invalid chat_user_id should 404
        response = self.client.get(
            reverse("chat", kwargs={"chat_user_id": 999}), follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_messages_view_missing_profile(self):
        """Test error handling when customer profile doesn't exist"""
        # Create a user without a customer profile
        user = User.objects.create_user(
            username="orphanuser", email="orphan@test.com", password="testpass123"
        )

        self.client.login(username="orphanuser", password="testpass123")
        response = self.client.get(reverse("messages inbox"))

        # Verify error message is shown (matches view exactly)
        self.assertEqual(response.context["error"], "Your profile could not be found.")
        # Verify empty conversation data
        self.assertEqual(response.context["conversations"], [])
        self.assertIsNone(response.context["active_chat"])
        self.assertEqual(response.context["messages"], [])

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

    def test_send_message_orphaned_user(self):
        """Test error handling when user has no Customer or Restaurant profile"""
        # Create user without any profile
        orphan_user = User.objects.create_user(
            username="orphan", email="orphan@test.com", password="testpass123"
        )

        self.client.login(username="orphan", password="testpass123")
        response = self.client.post(
            reverse("send_message", kwargs={"chat_user_id": self.customer1.id}),
            {"message": "Test message"},
        )

        # Verify error response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode(), "Sender not found")

        # Verify error message was added
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Your account was not found. Please contact support."
        )

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

    def test_send_message_generic_success(self):
        """Test successful message sending via generic endpoint"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("send_message_generic"),
            {"recipient": "user2@test.com", "message": "Test message"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            DM.objects.filter(sender=self.customer1, receiver=self.customer2).exists()
        )

    def test_send_message_generic_orphaned_user(self):
        """Test error when sender has no profile"""
        orphan_user = User.objects.create_user(
            username="orphan", email="orphan@test.com", password="testpass123"
        )
        self.client.login(username="orphan", password="testpass123")
        response = self.client.post(
            reverse("send_message_generic"),
            {"recipient": "user1@test.com", "message": "Test message"},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]), "Your account was not found. Please contact support."
        )

    def test_send_message_generic_missing_recipient(self):
        """Test error when recipient email is missing"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("send_message_generic"), {"message": "Test message"}
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Please enter a recipient email address.")

    def test_send_message_generic_empty_message(self):
        """Test error when message is empty"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("send_message_generic"),
            {"recipient": "user2@test.com", "message": ""},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Message cannot be empty.")

    def test_send_message_generic_self_message(self):
        """Test error when messaging self"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("send_message_generic"),
            {"recipient": "user1@test.com", "message": "Test message"},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "You can't message yourself.")

    def test_send_message_generic_restaurant_recipient(self):
        """Test error when recipient is a restaurant"""
        restaurant = Restaurant.objects.create(
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
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("send_message_generic"),
            {"recipient": "restaurant@test.com", "message": "Test message"},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            "'restaurant@test.com' is a restaurant account. Currently, you can only message customer accounts.",
        )

    def test_send_message_generic_invalid_recipient(self):
        """Test error when recipient doesn't exist"""
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            reverse("send_message_generic"),
            {"recipient": "nonexistent@test.com", "message": "Test message"},
        )
        self.assertEqual(response.status_code, 302)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(
            str(messages[0]),
            "Recipient 'nonexistent@test.com' does not exist. Please check the email address and try again.",
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

    def test_has_unread_messages_unauthenticated(self):
        """Test with unauthenticated/anonymous users"""
        from django.contrib.auth.models import AnonymousUser

        self.assertFalse(has_unread_messages(None))
        self.assertFalse(has_unread_messages(AnonymousUser()))

    def test_has_unread_messages_no_customer(self):
        """Test when user has no associated customer"""
        user = User.objects.create_user("no_customer@test.com", "password")
        self.assertFalse(has_unread_messages(user))

    def test_has_unread_messages_read_status(self):
        """Test read/unread message detection"""
        # Create read message
        DM.objects.create(
            sender=self.customer2, receiver=self.customer1, message=b"read", read=True
        )
        self.assertFalse(has_unread_messages(self.user1))

        # Create unread message
        DM.objects.create(
            sender=self.customer2,
            receiver=self.customer1,
            message=b"unread",
            read=False,
        )
        self.assertTrue(has_unread_messages(self.user1))

        # Mark as read and verify
        DM.objects.filter(receiver=self.customer1).update(read=True)
        self.assertFalse(has_unread_messages(self.user1))


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
            reverse("restaurant_detail", args=[self.restaurant.id])
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
            reverse("restaurant_detail", args=[self.restaurant.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_owner"])

    # using the restaurant id for detail view and this test is no longer needed
    # def test_restaurant_detail_case_insensitive(self):
    #     """Test restaurant name matching is case insensitive"""
    #     self.client.login(username="user1", password="testpass123")
    #     response = self.client.get(
    #         reverse("restaurant_detail", args=["test restaurant"])
    #     )
    #     self.assertEqual(response.status_code, 200)

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


class AuthenticationTests(TestCase):
    """Tests for user authentication views (login, logout, register)"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.customer = Customer.objects.create(
            username="testuser", email="test@example.com"
        )

    def test_login_success(self):
        """Test successful login redirects to home"""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "testpass123"},
            follow=True,
        )
        self.assertRedirects(response, reverse("home"))

    def test_login_failure(self):
        """Test failed login shows error"""
        response = self.client.post(
            reverse("login"),
            {"username": "testuser", "password": "wrongpass"},
            follow=True,
        )
        self.assertContains(response, "Invalid username or password")
        self.assertRedirects(response, reverse("landing"))

    def test_logout(self):
        """Test logout redirects to landing page"""
        self.client.login(username="testuser", password="testpass123")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, "/")

    def test_register_success(self):
        """Test successful registration"""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "Testpass123!",
                "password2": "Testpass123!",
            },
        )
        self.assertRedirects(response, "/home/")
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    def test_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "new@example.com",
                "password1": "Testpass123!",
                "password2": "Different123!",
            },
            follow=True,
        )
        self.assertContains(response, "Passwords do not match")

    def test_register_username_already_taken(self):
        """Test registration fails when username is already taken"""
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",  # Same as existing user
                "email": "new@example.com",
                "password1": "Testpass123!",
                "password2": "Testpass123!",
            },
            follow=True,
        )
        self.assertContains(response, "Username already taken")
        self.assertEqual(response.status_code, 200)  # Should stay on same page

    def test_register_email_already_taken(self):
        """Test registration fails when email is already taken"""
        response = self.client.post(
            reverse("register"),
            {
                "username": "newuser",
                "email": "test@example.com",
                "password1": "Testpass123!",
                "password2": "Testpass123!",
            },
            follow=True,
        )
        self.assertContains(response, "Email is already in use")
        self.assertEqual(response.status_code, 200)  # Should stay on same page


class SmokeTests(TestCase):
    """Basic smoke tests to verify views load without errors"""

    def test_landing_view(self):
        response = self.client.get(reverse("landing"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "landing.html")

    def test_home_view_authenticated(self):
        user = User.objects.create_user(
            username="test", email="test@example.com", password="test123"
        )
        self.client.force_login(user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")

    def test_dynamic_map_view(self):
        user = User.objects.create_user(
            username="test", email="test@example.com", password="test123"
        )
        self.client.force_login(user)
        response = self.client.get(reverse("dynamic-map"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "maps/nycmap_dynamic.html")


class RestaurantVerificationTests(TestCase):
    """Tests for restaurant verification and registration"""

    def setUp(self):
        self.client = Client()
        # Create existing user and restaurant for testing conflicts
        self.user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="testpass123",
        )
        self.restaurant = Restaurant.objects.create(
            id=1,
            name="Test Restaurant",
            username="restaurant1",
            email="restaurant@test.com",
            borough=1,
            building=123,
            street="Test St",
            zipcode="10001",
            phone="123-456-7890",
            cuisine_description="American",
            hygiene_rating=1,
            violation_description="No violations",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.966, 40.78),
        )
        self.valid_restaurant = Restaurant.objects.create(
            id=2,
            name="Valid Restaurant",
            username="",
            email="",
            borough=1,
            building=456,
            street="Valid St",
            zipcode="10002",
            phone="987-654-3210",
            cuisine_description="Italian",
            hygiene_rating=0,
            violation_description="__",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.985, 40.758),
        )

    def test_password_mismatch(self):
        """Test verification fails when passwords don't match"""
        response = self.client.post(
            reverse("restaurant_verify"),
            {
                "restaurant": "2",
                "username": "newuser",
                "email": "new@example.com",
                "password": "Testpass123!",
                "confirm_password": "Mismatch123!",
                "verify": "0000",  # Default verification code
            },
            follow=True,
        )
        self.assertContains(response, "Passwords do not match.")

    def test_invalid_verification_code(self):
        """Test verification fails with wrong code"""
        response = self.client.post(
            reverse("restaurant_verify"),
            {
                "restaurant": "2",
                "username": "newuser",
                "email": "new@example.com",
                "password": "Testpass123!",
                "confirm_password": "Testpass123!",
                "verify": "wrongcode",
            },
            follow=True,
        )
        self.assertContains(response, "Invalid verification code.")

    def test_username_taken(self):
        """Test verification fails when username exists"""
        response = self.client.post(
            reverse("restaurant_verify"),
            {
                "restaurant": "2",
                "username": "existinguser",
                "email": "new@example.com",
                "password": "Testpass123!",
                "confirm_password": "Testpass123!",
                "verify": "1234",
            },
            follow=True,
        )
        self.assertContains(response, "Username is already taken.")

    def test_email_taken(self):
        """Test verification fails when email exists"""
        response = self.client.post(
            reverse("restaurant_verify"),
            {
                "restaurant": "2",
                "username": "newuser",
                "email": "existing@example.com",
                "password": "Testpass123!",
                "confirm_password": "Testpass123!",
                "verify": "1234",
            },
            follow=True,
        )
        self.assertContains(response, "Email is already registered.")

    def test_restaurant_not_found(self):
        """Test verification fails when restaurant doesn't exist"""
        response = self.client.post(
            reverse("restaurant_verify"),
            {
                "restaurant": "999",  # Non-existent ID
                "username": "newuser",
                "email": "new@example.com",
                "password": "Testpass123!",
                "confirm_password": "Testpass123!",
                "verify": "1234",
            },
            follow=True,
        )
        self.assertContains(response, "Selected restaurant does not exist.")


class BookmarksTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="user1", password="testpass123", email="user1@test.com"
        )
        self.customer = Customer.objects.create(
            username="user1", email="user1@test.com", first_name="User", last_name="One"
        )
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            username="restaurant1",
            email="restaurant@test.com",
            borough=1,  # Manhattan
            building=123,
            street="Test St",
            zipcode="10001",
            phone="123-456-7890",
            cuisine_description="American",
            hygiene_rating=1,
            violation_description="No violations",
            inspection_date="2023-01-01",
            geo_coords=Point(-73.966, 40.78),
        )
        self.bookmarks_url = reverse("bookmarks_view")

    def test_bookmark_view_requires_login(self):
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_add_bookmark_success(self):
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            self.bookmarks_url, {"restaurant_id": self.restaurant.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertTrue(
            FavoriteRestaurant.objects.filter(
                customer=self.customer, restaurant=self.restaurant
            ).exists()
        )

    def test_add_duplicate_bookmark(self):
        FavoriteRestaurant.objects.create(
            customer=self.customer, restaurant=self.restaurant
        )
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            self.bookmarks_url, {"restaurant_id": self.restaurant.id}
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    def test_add_bookmark_invalid_restaurant(self):
        self.client.login(username="user1", password="testpass123")
        response = self.client.post(
            self.bookmarks_url, {"restaurant_id": 9999}  # Non-existent ID
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["success"])

    def test_get_bookmarks_empty(self):
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["restaurants"]), 0)
        self.assertEqual(data["count"], 0)

    def test_get_bookmarks_with_data(self):
        FavoriteRestaurant.objects.create(
            customer=self.customer, restaurant=self.restaurant
        )
        self.client.login(username="user1", password="testpass123")
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["restaurants"]), 1)
        self.assertEqual(data["count"], 1)
        self.assertEqual(data["restaurants"][0]["name"], "Test Restaurant")

    def test_missing_customer_profile(self):
        # Create user without customer profile
        user2 = User.objects.create_user(
            username="user2", password="testpass123", email="testuser2@test.com"
        )
        self.client.login(username="user2", password="testpass123")
        response = self.client.get(self.bookmarks_url)
        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.json())
