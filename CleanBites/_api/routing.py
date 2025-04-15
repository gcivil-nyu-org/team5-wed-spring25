from django.urls import path
from .consumers import ChatConsumer  # Replace with your consumer

websocket_urlpatterns = [
    path("ws/chat/<int:receiver_id>/", ChatConsumer.as_asgi()),  # Example WebSocket route
]