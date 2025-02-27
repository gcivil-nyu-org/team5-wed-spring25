from django.urls import path, include

urlpatterns = [
    path('restaurants/', include('_api._restaurants.urls')),  # Link `_restaurants` API
]