from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.landing_view, name="landing"),
    path("home/", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("nycmap/", views.nycmap_view, name="nycmap"),
    path(
        "restaurant/<str:name>/",
        views.restaurant_detail,
        name="restaurant_detail",
    ),
]
