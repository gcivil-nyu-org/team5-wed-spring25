from django.shortcuts import render
from rest_framework import viewsets, generics
from .serializers import RestaurantSerializer
from .models import Restaurant

# Create your views here.
class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

class RestaurantListView(generics.ListAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer