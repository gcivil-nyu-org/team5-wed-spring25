from django.shortcuts import render
from rest_framework import viewsets, generics, filters
from .serializers import (
    RestaurantSerializer,
    RestaurantAddressSerializer,
    CommentSerializer,
    ReplySerializer,
)
from .models import Restaurant, Comment, Reply
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.views import View

from utils import (
    get_restaurants,
    restaurant_to_feature,
    create_nyc_map,
)


# Create your views here.
class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    # Filters: allow ?borough=1 or ?cuisine_description=Pizza
    filterset_fields = ["borough", "cuisine_description", "hygiene_rating"]

    # Search: allow ?search=Joe's Diner (search in name and street)
    search_fields = ["name", "street"]

    # Ordering: allow ?ordering=inspection_date (or ?ordering=-inspection_date for descending)
    ordering_fields = ["inspection_date", "hygiene_rating"]


class RestaurantListView(generics.ListAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer


class RestaurantAddressListView(generics.ListAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantAddressSerializer


class RestaurantGeoJSONView(APIView):
    def get(self, request):
        restaurants = get_restaurants(request)
        features = [restaurant_to_feature(r) for r in restaurants]
        geojson_data = {"type": "FeatureCollection", "features": features}
        return Response(geojson_data)


class DynamicNYCMapView(View):
    def get(self, request):
        restaurants = get_restaurants(request)
        features = [restaurant_to_feature(r) for r in restaurants]
        m = create_nyc_map(features)
        return HttpResponse(m.get_root().render())


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["restaurant", "commenter", "flagged"]
    search_fields = ["comment"]
    ordering_fields = ["posted_at", "karma"]


class ReplyViewSet(viewsets.ModelViewSet):
    queryset = Reply.objects.all()
    serializer_class = ReplySerializer
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields = ["comment", "commenter", "flagged"]
    search_fields = ["reply"]
    ordering_fields = ["posted_at", "karma"]
