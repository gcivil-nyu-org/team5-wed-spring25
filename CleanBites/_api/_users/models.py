from django.db import models


class Customer(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Moderator(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DM(models.Model):
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(
        Customer, related_name="sent_dms", on_delete=models.CASCADE
    )
    receiver = models.ForeignKey(
        Customer, related_name="received_dms", on_delete=models.CASCADE
    )
    message = models.BinaryField()  # BYTEA for binary message storage
    flagged = models.BooleanField(default=False)
    flagged_by = models.ForeignKey(
        Moderator, null=True, blank=True, on_delete=models.SET_NULL
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)  # Track if message has been read

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~models.Q(sender=models.F("receiver")),
                name="chk_dm_sender_receiver",  # Prevent sending DMs to self
            )
        ]

    def __str__(self):
        return f"DM from {self.sender} to {self.receiver} at {self.sent_at}"


class FavoriteRestaurant(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    restaurant = models.ForeignKey("_restaurants.Restaurant", on_delete=models.CASCADE)

    class Meta:
        unique_together = ("customer", "restaurant")  # Enforces unique pairs in the DB

    def __str__(self):
        return f"{self.customer} likes {self.restaurant}"
