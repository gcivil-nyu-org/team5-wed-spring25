from django.db import models
from django.contrib.gis.db import models as GISmodels
from django.contrib.gis.geos import Point
from django.urls import reverse


# Create your models here.
class Restaurant(models.Model):
    id = models.AutoField(primary_key=True)  # SERIAL in PostgreSQL
    name = models.CharField(max_length=255)  # Restaurant name
    email = models.EmailField(max_length=255)  # Email field
    phone = models.CharField(max_length=15)  # Phone number
    menu = models.BinaryField(
        null=True, blank=True
    )  # BYTEA for binary data (menu file)
    building = models.IntegerField()  # Building number
    street = models.CharField(max_length=255)  # Street name
    zipcode = models.CharField(max_length=10)  # Zip code
    hygiene_rating = models.IntegerField()  # Hygiene rating
    inspection_date = models.DateField()  # Inspection date
    borough = models.IntegerField()  # Borough ID
    cuisine_description = models.CharField(max_length=255)  # Cuisine type
    violation_description = models.TextField()  # Violation description
    geo_coords = GISmodels.PointField(default=Point(0.0, 0.0))  # latitude coord

    def __str__(self):
        return f"{self.name} ({self.street}, {self.zipcode})"


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    commenter = models.ForeignKey("_users.Customer", on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    comment = models.BinaryField(null=True, blank=True)  # BYTEA for binary data
    karma = models.IntegerField(default=0)
    flagged = models.BooleanField(default=False)
    flagged_by = models.ForeignKey(
        "_users.Moderator", null=True, blank=True, on_delete=models.SET_NULL
    )
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment {self.id} by {self.commenter}"


class Reply(models.Model):
    id = models.AutoField(primary_key=True)
    commenter = models.ForeignKey("_users.Customer", on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    reply = models.BinaryField(null=True, blank=True)  # BYTEA for binary data
    karma = models.IntegerField(default=0)
    flagged = models.BooleanField(default=False)
    flagged_by = models.ForeignKey(
        "_users.Moderator", null=True, blank=True, on_delete=models.SET_NULL
    )
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reply {self.id} to Comment {self.comment.id}"
