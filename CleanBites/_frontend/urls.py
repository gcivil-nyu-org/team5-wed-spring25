from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("home/", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("restaurant_register/", views.restaurant_register, name="restaurant_register"),
    path(
        "restaurant_verify/",
        views.restaurant_verify,
        name="restaurant_verify",
    ),
    path("mapdynamic/", views.dynamic_map_view, name="dynamic-map"),
    path(
        "restaurant/<str:name>/",
        views.restaurant_detail,
        name="restaurant_detail",
    ),
]
