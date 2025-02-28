from django.shortcuts import render
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer
from .serializers import CustomerSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    # Filters: allow ?email=john@example.com or ?first_name=John
    filterset_fields = ['email', 'first_name', 'last_name']

    # Search: allow ?search=John (search in first name and last name)
    search_fields = ['first_name', 'last_name']

    # Ordering: allow ?ordering=first_name (or ?ordering=-first_name for descending)
    ordering_fields = ['first_name', 'last_name', 'email']
