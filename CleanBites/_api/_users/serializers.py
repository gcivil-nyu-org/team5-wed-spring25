from rest_framework import serializers
from .models import Customer, Moderator, DM, FavoriteRestaurant


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"  # Includes all fields in the Customer model


class ModeratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Moderator
        fields = "__all__"  # Includes all fields in the Moderator model


class DMSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.first_name", read_only=True)
    receiver_name = serializers.CharField(source="receiver.first_name", read_only=True)

    class Meta:
        model = DM
        fields = [
            "id",
            "sender",
            "sender_name",
            "receiver",
            "receiver_name",
            "message",
            "flagged",
            "flagged_by",
            "sent_at",
        ]


class FavoriteRestaurantSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.first_name", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)

    class Meta:
        model = FavoriteRestaurant
        fields = ["customer", "customer_name", "restaurant", "restaurant_name"]
