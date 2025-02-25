import folium
import requests


f = folium.Figure(width=1000, height=500)
m = folium.Map(location= (40.7128, -74.0060), tiles="openstreetmap",
zoom_start=10, min_zoom = 15).add_to(f)

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

# Fetch data from Overpass API
response = requests.get(overpass_url, params={'data': overpass_query})
data = response.json()

# Add restaurant locations to the map
for element in data['elements']:
    if 'lat' in element and 'lon' in element:  # Nodes have direct lat/lon
        lat, lon = element['lat'], element['lon']
    elif 'center' in element:  # Ways/Relations have a center
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
