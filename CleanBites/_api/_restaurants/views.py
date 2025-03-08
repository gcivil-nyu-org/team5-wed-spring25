from django.shortcuts import render
from rest_framework import viewsets, generics, filters
from .serializers import RestaurantSerializer, RestaurantAddressSerializer, CommentSerializer, ReplySerializer
from .models import Restaurant, Comment, Reply
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
                    "coordinates": [
                        restaurant.geo_coords.x if restaurant.geo_coords else 0,  # Longitude (X)
                        restaurant.geo_coords.y if restaurant.geo_coords else 0   # Latitude (Y)
                    ]
                },
                "properties": {
                    "name": restaurant.name,
                    "address": f"{restaurant.building} {restaurant.street}, {restaurant.zipcode}",
                    "borough": restaurant.borough,
                    "cuisine": restaurant.cuisine_description,
                    "rating": restaurant.hygiene_rating
                }
            })

        return Response(geojson_data)
    
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['restaurant', 'commenter', 'flagged']
    search_fields = ['comment']
    ordering_fields = ['posted_at', 'karma']

class ReplyViewSet(viewsets.ModelViewSet):
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    filterset_fields = ['comment', 'commenter', 'flagged']
    search_fields = ['reply']
    ordering_fields = ['posted_at', 'karma']

