from django.db import models

# Create your models here.
class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    cuisine = models.CharField(max_length=255, blank=True, null=True)
    hygiene_rating = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    profile_image = models.ImageField(upload_to='restaurant_profiles/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name