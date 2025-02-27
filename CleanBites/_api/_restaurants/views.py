from django.shortcuts import render
from rest_framework import viewsets, generics, filters
from .serializers import RestaurantSerializer, RestaurantAddressSerializer
from .models import Restaurant
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView

# Create your views here.
class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filters: allow ?borough=1 or ?cuisine_description=Pizza
    filterset_fields = ['borough', 'cuisine_description', 'hygiene_rating']

    # Search: allow ?search=Joe's Diner (search in name and street)
    search_fields = ['name', 'street']

    # Ordering: allow ?ordering=inspection_date (or ?ordering=-inspection_date for descending)
    ordering_fields = ['inspection_date', 'hygiene_rating']

class RestaurantListView(generics.ListAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

class RestaurantAddressListView(generics.ListAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantAddressSerializer

class RestaurantGeoJSONView(APIView):
    """Returns restaurant data as GeoJSON format for mapping"""

    def get(self, request):
        restaurants = Restaurant.objects.all()
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }

        for restaurant in restaurants:
            geojson_data["features"].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [0, 0]  # Placeholder for lat/lon
                },
                "properties": {
                    "name": restaurant.name,
                    "address": f"{restaurant.building} {restaurant.street}, {restaurant.zipcode}",
                    "borough": restaurant.borough,
                    "cuisine": restaurant.cuisine_description
                }
            })

        return Response(geojson_data)