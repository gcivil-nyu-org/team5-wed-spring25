# Generated by Django 4.2.20 on 2025-04-09 21:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("_restaurants", "0006_restaurant_is_activated"),
    ]

    operations = [
        migrations.AlterField(
            model_name="restaurant",
            name="is_activated",
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
    ]
