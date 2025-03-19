from django.shortcuts import render
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer, Moderator, DM, FavoriteRestaurant
from .serializers import (
    CustomerSerializer,
    ModeratorSerializer,
    DMSerializer,
    FavoriteRestaurantSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Filters: allow ?email=john@example.com or ?first_name=John
    filterset_fields = ["email", "first_name", "last_name"]

    # Search: allow ?search=John (search in first name and last name)
    search_fields = ["first_name", "last_name"]

    # Ordering: allow ?ordering=first_name (or ?ordering=-first_name for descending)
    ordering_fields = ["first_name", "last_name", "email"]


class ModeratorViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows moderators to be viewed or edited.
    """

    queryset = Moderator.objects.all()
    serializer_class = ModeratorSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Filters: allow ?email=admin@example.com or ?first_name=John
    filterset_fields = ["email", "first_name", "last_name"]

    # Search: allow ?search=John (search in first name and last name)
    search_fields = ["first_name", "last_name"]

    # Ordering: allow ?ordering=first_name
    ordering_fields = ["first_name", "last_name", "email"]


class DMViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows direct messages (DMs) to be viewed or edited.
    """

    queryset = DM.objects.all()
    serializer_class = DMSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Filters: allow ?sender=1 or ?receiver=2
    filterset_fields = ["sender", "receiver", "flagged"]

    # Search: allow ?search=message (binary field so not applicable, but can be used for metadata)
    search_fields = []

    # Ordering: allow ?ordering=sent_at
    ordering_fields = ["sent_at"]


class FavoriteRestaurantViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows favorite restaurants to be managed.
    """

    queryset = FavoriteRestaurant.objects.all()
    serializer_class = FavoriteRestaurantSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Filters: allow ?customer=1 or ?restaurant=2
    filterset_fields = ["customer", "restaurant"]

    # Search: allow ?search=restaurant_name (not needed as we filter by ID)
    search_fields = []

    # Ordering: No explicit ordering needed
    ordering_fields = []
