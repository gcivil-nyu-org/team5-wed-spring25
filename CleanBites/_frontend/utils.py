from _api._users.models import Customer, DM
from django.db.models import Q
import logging

# Get logger
logger = logging.getLogger(__name__)


def has_unread_messages(user):
    """Check if a user has any unread messages."""
    if not user or not user.is_authenticated:
        logger.debug(f"User not authenticated, returning False")
        return False

    try:
        customer = Customer.objects.get(email=user.email)
        has_unread = DM.objects.filter(receiver=customer, read=False).exists()
        logger.debug(f"User {user.email} has unread messages: {has_unread}")
        return has_unread
    except Customer.DoesNotExist:
        logger.debug(f"Customer with email {user.email} does not exist")
        return False
    except Exception as e:
        logger.error(f"Error checking unread messages: {str(e)}")
        return False


import os
import requests
import folium
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import Distance
from _api._restaurants.models import Restaurant  # adjust import as needed
from shapely.geometry import shape, Point as ShapelyPoint
from django.conf import settings

# Load NYC boundary from GeoJSON
NYC_GEOJSON_URL = (
    "https://raw.githubusercontent.com/dwillis/nyc-maps/master/boroughs.geojson"
)
nyc_geojson = requests.get(NYC_GEOJSON_URL).json()
nyc_polygons = [shape(feature["geometry"]) for feature in nyc_geojson["features"]]


def is_in_nyc(lat, lon):
    """Check if a point is inside NYC boroughs using GeoJSON data."""
    point = ShapelyPoint(lon, lat)  # Shapely uses (lon, lat) order
    return any(polygon.contains(point) for polygon in nyc_polygons)


# get restaurants
# can filter based on query parameter
def get_restaurants(request):
    restaurants = Restaurant.objects.all()
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    distance = request.GET.get("distance")
    name_filter = request.GET.get("name")
    rating_filter = request.GET.get("rating")
    cuisine_filter = request.GET.get("cuisine")
    if lat and lng and distance:
        try:
            user_location = Point(float(lng), float(lat), srid=4326)
            distance_val = float(distance)
            restaurants = restaurants.filter(
                geo_coords__distance_lte=(user_location, Distance(km=distance_val))
            )
        except ValueError:
            return Response(
                {"error": "Invalid latitude, longitude, or distance"}, status=400
            )
    if name_filter:
        restaurants = restaurants.filter(name__icontains=name_filter)
    if rating_filter:
        try:
            rating_int = int(rating_filter)
            restaurants = restaurants.filter(hygiene_rating=rating_int)
        except ValueError:
            return Response({"error": "Invalid hygiene rating"}, status=400)
    if cuisine_filter:
        restaurants = restaurants.filter(cuisine_description__icontains=cuisine_filter)
    return restaurants


# convert Restaurant instance to a GeoJSON feature
def restaurant_to_feature(restaurant):
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [
                restaurant.geo_coords.x if restaurant.geo_coords else 0,
                restaurant.geo_coords.y if restaurant.geo_coords else 0,
            ],
        },
        "properties": {
            "name": restaurant.name,
            "address": f"{restaurant.building} {restaurant.street}, {restaurant.zipcode}",
            "borough": restaurant.borough,
            "cuisine": restaurant.cuisine_description,
            "rating": restaurant.hygiene_rating,
        },
    }


# return marker color based on the hygiene rating
def get_color(rating):
    try:
        rating = int(rating)
        if 0 <= rating <= 13:
            return "green"
        elif 14 <= rating <= 30:
            return "orange"
        elif 31 <= rating <= 50:
            return "red"
        else:
            return "blue"
    except (ValueError, TypeError):
        return "blue"


# create Folium map
def create_nyc_map(features):
    f = folium.Figure(width=1000, height=500)
    m = folium.Map(
        location=(40.7128, -74.0060), tiles="openstreetmap", zoom_start=12, min_zoom=10
    ).add_to(f)
    for feature in features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        if geometry.get("type") == "Point":
            coordinates = geometry.get("coordinates", [])
            if not coordinates or len(coordinates) < 2:
                continue
            lon, lat = coordinates[0], coordinates[1]
            if lat is not None and lon is not None and is_in_nyc(lat, lon):
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; width: 250px; padding: 5px;">
                    <div style="font-size: 14pt; font-weight: bold; margin-bottom: 4px;">
                    <a href="{settings.BASE_URL}restaurant/{properties.get("name", "Unnamed Restaurant")}/"
                      target="_blank"
                    style="text-decoration: none; color: #1a73e8;">
                        {properties.get("name", "Unnamed Restaurant")}
                    </a>
                    </div>
                    <div style="font-size: 10pt; margin-bottom: 4px;">
                        Cuisine: {properties.get("cuisine", "N/A")}
                    </div>
                    <div style="font-size: 10pt; margin-bottom: 8px;">
                        Address: {properties.get("address", "N/A")}
                    </div>
                    <hr style="margin: 4px 0;">
                    <div style="font-size: 10pt;">
                        <strong>Hygiene Rating:</strong> {properties.get("rating", "N/A")}
                    </div>
                </div>
                """
                iframe_height = 170 if properties.get("address") else 150
                iframe = folium.IFrame(html=popup_html, width=270, height=iframe_height)
                popup = folium.Popup(iframe, max_width="auto")
                color = get_color(properties.get("rating", -1))
                folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
                ).add_to(m)
    return m
