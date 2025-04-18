# Generated by Django 4.2.20 on 2025-04-13 16:23

from django.conf import settings
import django.contrib.gis.db.models.fields
import django.contrib.gis.geos.point
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("_restaurants", "0009_restaurant_deactivation_reason"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="restaurant",
            name="deactivation_reason",
        ),
        migrations.RemoveField(
            model_name="restaurant",
            name="is_activated",
        ),
        migrations.CreateModel(
            name="RestaurantDeactivated",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("username", models.CharField(blank=True, max_length=255, null=True)),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(max_length=255)),
                ("phone", models.CharField(max_length=15)),
                ("menu", models.BinaryField(blank=True, null=True)),
                ("building", models.IntegerField()),
                ("street", models.CharField(max_length=255)),
                ("zipcode", models.CharField(max_length=10)),
                ("hygiene_rating", models.IntegerField()),
                ("inspection_date", models.DateField()),
                ("borough", models.IntegerField()),
                ("cuisine_description", models.CharField(max_length=255)),
                ("violation_description", models.TextField()),
                (
                    "geo_coords",
                    django.contrib.gis.db.models.fields.PointField(
                        default=django.contrib.gis.geos.point.Point(0.0, 0.0), srid=4326
                    ),
                ),
                (
                    "is_activated",
                    models.BooleanField(blank=True, default=True, null=True),
                ),
                ("deactivation_reason", models.TextField(blank=True, null=True)),
                (
                    "user",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="restaurant_deactivated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
