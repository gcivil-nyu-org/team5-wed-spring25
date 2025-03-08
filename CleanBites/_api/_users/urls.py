from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ModeratorViewSet, DMViewSet, FavoriteRestaurantViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'moderators', ModeratorViewSet, basename='moderator')
router.register(r'dms', DMViewSet, basename='dm')
router.register(r'favorites', FavoriteRestaurantViewSet, basename='favorite-restaurant')

urlpatterns = [
    path('', include(router.urls)),
]
