import folium
import requests
import json
import random

from shapely.geometry import shape, Point

# Load NYC boundary from GeoJSON
NYC_GEOJSON_URL = (
    "https://raw.githubusercontent.com/dwillis/nyc-maps/master/boroughs.geojson"
)
nyc_geojson = requests.get(NYC_GEOJSON_URL).json()

# Convert NYC boroughs to Shapely polygons
nyc_polygons = [shape(feature["geometry"]) for feature in nyc_geojson["features"]]


def is_in_nyc(lat, lon):
    """Check if a point is inside NYC boroughs using GeoJSON data."""
    point = Point(lon, lat)  # Shapely uses (lon, lat) order
    return any(polygon.contains(point) for polygon in nyc_polygons)


# Create NYC Map
f = folium.Figure(width=1000, height=500)
m = folium.Map(
    location=(40.7128, -74.0060), tiles="openstreetmap", zoom_start=12, min_zoom=10
).add_to(f)

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
response = requests.get(overpass_url, params={"data": overpass_query})
data = response.json()

# Reduce markers & filter only NYC locations
filtered_elements = [
    element
    for element in data["elements"][::12]  # Reduce density
    if (
        ("lat" in element and is_in_nyc(element["lat"], element["lon"]))
        or (
            "center" in element
            and is_in_nyc(element["center"]["lat"], element["center"]["lon"])
        )
    )
]


# Define a list of possible colors for markers
colors = ["green", "orange", "red"]

# Add NYC-Only Restaurants to the Map with random colors, hygiene ratings, and detailed popups
for element in filtered_elements:
    # Determine the latitude/longitude

    if "lat" in element and "lon" in element:
        lat, lon = element["lat"], element["lon"]
    elif "center" in element:
        lat, lon = element["center"]["lat"], element["center"]["lon"]
    else:
        continue

    # Extract tags and details
    tags = element.get("tags", {})
    name = tags.get("name", "Unnamed Restaurant")
    cuisine = tags.get("cuisine", "Cuisine not available")

    # Build address from available address tags
    addr_housenumber = tags.get("addr:housenumber", "")
    addr_street = tags.get("addr:street", "")
    addr_city = tags.get("addr:city", "")
    address_parts = []
    street_info = f"{addr_housenumber} {addr_street}".strip()
    if street_info:
        address_parts.append(street_info)
    if addr_city:
        address_parts.append(addr_city)
    address = ", ".join(address_parts) if address_parts else "Address not available"

    # Randomly select a color from the list
    color = random.choice(colors)

    # Determine hygiene rating based on marker color
    if color == "green":
        hygiene_rating = "A"
    elif color == "orange":
        hygiene_rating = "B"
    else:  # color == "red"
        hygiene_rating = "C"

    popup_html = f"""
    <div style="font-family: Arial, sans-serif; width: 250px; padding: 5px;">
      <!-- Title / Name -->
      <div style="font-size: 14pt; font-weight: bold; color: #202124; margin-bottom: 4px;">
        {name}
      </div>
      <!-- Subtitle / Cuisine -->
      <div style="font-size: 10pt; color: #70757a; margin-bottom: 4px;">
        Cuisine: {cuisine}
      </div>
      <!-- Address -->
      <div style="font-size: 10pt; color: #70757a; margin-bottom: 8px;">
        Address: {address}
      </div>
      <hr style="margin: 4px 0;">
      <!-- Hygiene Rating -->
      <div style="font-size: 10pt;">
        <strong>Hygiene Rating:</strong> {hygiene_rating}
      </div>
    </div>
    """

    # Wrap the HTML in an IFrame, so we can set a custom size
    iframe = folium.IFrame(html=popup_html, width=260, height=140)
    popup = folium.Popup(iframe, max_width=300)

    # Add marker to map with the randomly chosen color, the custom popup, and cutlery icon
    folium.Marker(
        location=[lat, lon],
        popup=popup,
        icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
    ).add_to(m)

# Save the map to an HTML file
m.save("templates/maps/nycmap.html")
