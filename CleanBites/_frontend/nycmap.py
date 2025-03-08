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

# Fetch Data from Local API
local_api_url = "http://localhost:8000/api/restaurants/geojson/"
response = requests.get(local_api_url)
data = response.json()

# Extract features list from FeatureCollection
features = data.get("features", [])

# Define color mapping based on hygiene rating
def get_color(rating):
    try:
        rating = int(rating)
        if 0 <= rating <= 13:
            return "green"  # A
        elif 14 <= rating <= 30:
            return "orange"  # B
        elif 31 <= rating <= 50:
            return "red"  # C
        else:
            return "blue"  # Unknown rating
    except (ValueError, TypeError):
        return "blue"  # Default for invalid ratings

# Iterate through the GeoJSON features and add markers
for feature in features:
    geometry = feature.get("geometry", {})
    properties = feature.get("properties", {})
    
    if geometry.get("type") == "Point":
        lon, lat = geometry.get("coordinates", [None, None])
        
        if lat is not None and lon is not None and is_in_nyc(lat, lon):
            name = properties.get("name", "Unnamed Restaurant")
            address = properties.get("address", "Address not available")
            cuisine = properties.get("cuisine", "Cuisine not available")
            rating = properties.get("rating", -1)  # Default to -1 if missing
            color = get_color(rating)
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; width: 250px; padding: 5px;">
              <a href="/restaurant/{properties.get('id', 0)}/" target="_blank" style="text-decoration: none; color: #1a73e8;">
                {name}
              </div>
              <div style="font-size: 10pt; color: #70757a; margin-bottom: 4px;">
                Cuisine: {cuisine}
              </div>
              <div style="font-size: 10pt; color: #70757a; margin-bottom: 8px;">
                Address: {address}
              </div>
              <hr style="margin: 4px 0;">
              <div style="font-size: 10pt;">
                <strong>Hygiene Rating:</strong> {rating}
              </div>
            </div>
            """

            iframe = folium.IFrame(html=popup_html, width=260, height=140)
            popup = folium.Popup(iframe, max_width=300)

            folium.Marker(
                location=[lat, lon],
                popup=popup,
                icon=folium.Icon(color=color, icon="cutlery", prefix="fa")
            ).add_to(m)

# Save the map to an HTML file
m.save('templates/maps/nycmap.html')
