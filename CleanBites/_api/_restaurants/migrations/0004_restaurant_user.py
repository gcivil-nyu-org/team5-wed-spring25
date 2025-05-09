# Generated by Django 4.2.20 on 2025-03-30 06:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("_restaurants", "0003_restaurant_geo_coords"),
    ]

    operations = [
        migrations.AddField(
            model_name="restaurant",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="restaurant",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
