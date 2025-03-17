# ensure Django loads apps before importing models
import os
import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "CleanBites.settings")
django.setup()

from utils import create_nyc_map

# URL for the RestaurantGeoJSONView endpoint
api_host = os.environ.get("API_HOST", "api")
api_url = f"http://{api_host}:8000/api/restaurants/geojson/"
base_url = f"http://localhost:8000/restaurant/"
# Pull restaurant data via the API (no query parameters for the static weekly update)
response = requests.get(api_url)
data = response.json()
features = data.get("features", [])

# Create a folium map centered on NYC
m = create_nyc_map(features, base_url)

# Save the map to an HTML file in the templates folder
current_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(current_dir, "templates", "maps", "nycmap.html")
os.makedirs(os.path.dirname(output_file), exist_ok=True)
m.save(output_file)
