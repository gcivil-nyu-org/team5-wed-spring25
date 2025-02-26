import folium
import requests
import json
from shapely.geometry import shape, Point

# Load NYC boundary from GeoJSON
NYC_GEOJSON_URL = "https://raw.githubusercontent.com/dwillis/nyc-maps/master/boroughs.geojson"
nyc_geojson = requests.get(NYC_GEOJSON_URL).json()

# Convert NYC boroughs to Shapely polygons
nyc_polygons = [shape(feature["geometry"]) for feature in nyc_geojson["features"]]

def is_in_nyc(lat, lon):
    """Check if a point is inside NYC boroughs using GeoJSON data."""
    point = Point(lon, lat)  # Shapely uses (lon, lat) order
    return any(polygon.contains(point) for polygon in nyc_polygons)

# Create NYC Map
f = folium.Figure(width=1000, height=500)
m = folium.Map(location=(40.7128, -74.0060), tiles="openstreetmap",
               zoom_start=12, min_zoom=10).add_to(f)

# Overpass API Query
overpass_url = "http://overpass-api.de/api/interpreter"
overpass_query = """
[out:json][timeout:25];
(
  node["amenity"="restaurant"](40.4774,-74.2591,40.9176,-73.7004);
  way["amenity"="restaurant"](40.4774,-74.2591,40.9176,-73.7004);
  relation["amenity"="restaurant"](40.4774,-74.2591,40.9176,-73.7004);
);
out center;
"""

# Fetch Data from Overpass API
response = requests.get(overpass_url, params={'data': overpass_query})
data = response.json()

# Reduce markers & filter only NYC locations
filtered_elements = [
    element for element in data['elements'][::6]  # Reduce density
    if (
        ('lat' in element and is_in_nyc(element['lat'], element['lon'])) or
        ('center' in element and is_in_nyc(element['center']['lat'], element['center']['lon']))
    )
]

# Add NYC-Only Restaurants to the Map
for element in filtered_elements:
    if 'lat' in element and 'lon' in element:
        lat, lon = element['lat'], element['lon']
    elif 'center' in element:
        lat, lon = element['center']['lat'], element['center']['lon']
    else:
        continue

    # Get restaurant name if available
    name = element.get('tags', {}).get('name', 'Unnamed Restaurant')

    # Add marker to map
    folium.Marker(
        location=[lat, lon],
        popup=name,
        icon=folium.Icon(color="red", icon="cutlery", prefix="fa")
    ).add_to(m)

m.save('nycmap.html')
