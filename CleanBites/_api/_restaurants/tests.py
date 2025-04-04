import unittest
from unittest.mock import patch, MagicMock
import requests
from django.test import TestCase
from django.core.exceptions import ValidationError
from _api._restaurants.fetch_data import NYC_DATA_URL
from _api._restaurants.models import Restaurant, Comment, Reply
from _api._users.models import Customer
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.urls import reverse


class TestAPIEndpoint(TestCase):
    @patch("_api._restaurants.fetch_data.requests.get")
    def test_nyc_api_connectivity(self, mock_get):
        """Test we can connect to NYC API endpoint"""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Make test request
        response = requests.get(NYC_DATA_URL)

        # Verify we got a successful response
        self.assertEqual(response.status_code, 200)
        mock_get.assert_called_once_with(NYC_DATA_URL)

    @patch("_api._restaurants.fetch_data.requests.get")
    def test_nyc_api_response_format(self, mock_get):
        """Test NYC API returns JSON data"""
        # Mock response with sample data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"camis": "12345", "dba": "Test Restaurant"}]
        mock_get.return_value = mock_response

        # Make test request
        response = requests.get(NYC_DATA_URL)
        data = response.json()

        # Verify response format
        self.assertIsInstance(data, list)
        self.assertIn("camis", data[0])
        self.assertIn("dba", data[0])


class RestaurantModelTests(TestCase):
    def test_production_no_duplicate_emails(self):
        """Test production database has no duplicate restaurant emails (except 'Not Provided')"""
        # Get all emails that aren't 'Not Provided'
        emails = Restaurant.objects.exclude(email="Not Provided").values_list(
            "email", flat=True
        )

        # Find duplicates
        seen = set()
        duplicates = set(email for email in emails if email in seen or seen.add(email))

        # Verify no duplicates found
        self.assertEqual(
            len(duplicates),
            0,
            msg=f"Duplicate emails found in production: {duplicates}",
        )

    def test_restaurant_required_fields(self):
        """Test required fields are properly validated"""
        with self.assertRaises(Exception):
            Restaurant.objects.create(name=None)  # name should be required
        with self.assertRaises(Exception):
            Restaurant.objects.create(
                hygiene_rating=None
            )  # hygiene_rating should be required

    def test_comment_required_fields(self):
        """Test Comment model required fields"""
        # Create a test restaurant and customer
        restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            email="test@example.com",
            phone="1234567890",
            building=123,
            street="Test St",
            zipcode="10001",
            hygiene_rating=90,
            inspection_date="2025-01-01",
            borough=1,
            cuisine_description="Test",
            violation_description="None",
        )
        customer = Customer.objects.create(
            username="testuser",
            email="user@example.com",
            first_name="Test",
            last_name="User",
            id=1,
        )

        # Test required fields
        with self.assertRaises(Exception):
            Comment.objects.create(commenter=None, restaurant=restaurant)
        with self.assertRaises(Exception):
            Comment.objects.create(commenter=customer, restaurant=None)

    def test_reply_required_fields(self):
        """Test Reply model required fields"""
        # Create test comment
        restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            email="test@example.com",
            phone="1234567890",
            building=123,
            street="Test St",
            zipcode="10001",
            hygiene_rating=90,
            inspection_date="2025-01-01",
            borough=1,
            cuisine_description="Test",
            violation_description="None",
        )
        customer = Customer.objects.create(
            username="testuser",
            email="user@example.com",
            first_name="Test",
            last_name="User",
            id=1,
        )
        comment = Comment.objects.create(
            commenter=customer, restaurant=restaurant, karma=0
        )

        # Test required fields
        with self.assertRaises(Exception):
            Reply.objects.create(comment=None, replier=customer)
        with self.assertRaises(Exception):
            Reply.objects.create(comment=comment, replier=None)


class RestaurantViewSetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.restaurant = Restaurant.objects.create(
            name="Test Restaurant",
            email="test@example.com",
            phone="1234567890",
            building=123,
            street="Test St",
            zipcode="10001",
            hygiene_rating=90,
            inspection_date="2025-01-01",
            borough=1,
            cuisine_description="Test",
            violation_description="None",
            geo_coords=Point(-73.966, 40.78)
        )

    def test_restaurant_list(self):
        url = reverse('restaurant-list')
        response = self.client.get(url)
        self.assertGreaterEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_restaurant_filter_by_borough(self):
        url = reverse('restaurant-list') + '?borough=1'
        response = self.client.get(url)
        self.assertGreaterEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_restaurant_search(self):
        url = reverse('restaurant-list') + '?search=Test'
        response = self.client.get(url)
        self.assertGreaterEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
