from django.shortcuts import render
from rest_framework import viewsets, generics, filters
from .serializers import RestaurantSerializer, RestaurantAddressSerializer, CommentSerializer, ReplySerializer
from .models import Restaurant, Comment, Reply
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance

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
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        # distance should be in kilometers
        distance = request.GET.get('distance')

        if lat and lng and distance:
            print(f"Received lat: {lat}, {type(lat)}, lng: {lng}, {type(lng)}, distance: {distance}, {type(distance)}")
            try:
                user_location = Point(float(lng), float(lat), srid=4326)
                distance_val = float(distance)
                print("user_location:", user_location, type(user_location))
                print("distance_val:", distance_val, type(distance_val))
            except ValueError:
                return Response({
                                "error": "Invalid latitude, longitude, or distance"},
                                status = 400)
            restaurants = Restaurant.objects.filter(
                # geo_coords = geographic field in db
                # __distance_lte = spatial lookup filter
                    # checks if distance between "geo_coords" and "user_location" is lte to "distance"
                geo_coords__distance_lte=(user_location, Distance(km=distance_val))
            )
        else:
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

