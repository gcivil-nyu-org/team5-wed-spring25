from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ValidationError

from _api._users.models import Customer, DM
from _frontend.utils import has_unread_messages

User = get_user_model()

class MessageSystemTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1', 
            email='user1@test.com', 
            password='testpass123'
        )
        self.customer1 = Customer.objects.create(
            username='user1', 
            email='user1@test.com',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            username='user2', 
            email='user2@test.com', 
            password='testpass123'
        )
        self.customer2 = Customer.objects.create(
            username='user2', 
            email='user2@test.com',
            first_name='User',
            last_name='Two'
        )
        
        self.client = Client()
    
    def test_dm_creation(self):
        """Test basic DM creation"""
        dm = DM.objects.create(
            sender=self.customer1,
            receiver=self.customer2,
            message=b'Test message',
            read=False
        )
        self.assertEqual(dm.sender, self.customer1)
        self.assertEqual(dm.receiver, self.customer2)
        self.assertEqual(dm.message, b'Test message')
        self.assertFalse(dm.read)
        self.assertFalse(dm.flagged)
        self.assertIsNone(dm.flagged_by)
    
    def test_dm_self_send_prevention(self):
        """Test that users can't send DMs to themselves"""
        with self.assertRaises(ValidationError):
            dm = DM(
                sender=self.customer1,
                receiver=self.customer1,
                message=b'Test message'
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
            message=b'Test message',
            read=False
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
            message=b'Test message',
            read=False
        )
        
        # Login and view messages
        self.client.login(username='user1', password='testpass123')
        response = self.client.get(reverse('messages inbox'))
        
        # Message should now be marked as read
        self.assertFalse(DM.objects.filter(receiver=self.customer1, read=False).exists())
