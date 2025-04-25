import requests
from _api._restaurants.models import Restaurant  # adjust import as needed
from shapely.geometry import shape

# Load NYC boundary from GeoJSON
NYC_GEOJSON_URL = (
    "https://raw.githubusercontent.com/dwillis/nyc-maps/master/boroughs.geojson"
)
nyc_geojson = requests.get(NYC_GEOJSON_URL).json()
nyc_polygons = [shape(feature["geometry"]) for feature in nyc_geojson["features"]]
