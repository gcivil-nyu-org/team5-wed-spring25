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
    path("user/<str:username>/", views.user_profile, name="user_profile"),
    path(
        "update-profile/",
        views.update_restaurant_profile_view,
        name="update_restaurant_profile",
    ),
    path("inbox/", views.messages_view, name="messages inbox"),
    path("inbox/<int:chat_user_id>/", views.messages_view, name="chat"),
    path("inbox/send/", views.send_message_generic, name="send_message_generic"),
    path("inbox/send/<int:chat_user_id>/", views.send_message, name="send_message"),
    path(
        "inbox/delete/<int:other_user_id>/",
        views.delete_conversation,
        name="delete_conversation",
    ),
    path("profile/<str:username>/", views.profile_router, name="user_profile"),
    path(
        "debug/unread-messages/",
        views.debug_unread_messages,
        name="debug_unread_messages",
    ),
]
