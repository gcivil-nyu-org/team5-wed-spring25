from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, RestaurantListView

router = DefaultRouter()
router.register(r'router', RestaurantViewSet)  # Maps API to ViewSet

urlpatterns = [
    path('', include(router.urls)),  # Include the router URLs
    path('list/', RestaurantListView.as_view(), name='restaurant-list'),
]
