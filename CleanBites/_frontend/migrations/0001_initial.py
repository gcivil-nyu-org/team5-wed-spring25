# Generated by Django 4.2.20 on 2025-03-14 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Restaurant",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("address", models.TextField()),
                ("cuisine", models.CharField(blank=True, max_length=255, null=True)),
                ("hygiene_rating", models.IntegerField()),
                ("latitude", models.FloatField()),
                ("longitude", models.FloatField()),
                (
                    "profile_image",
                    models.ImageField(
                        blank=True, null=True, upload_to="restaurant_profiles/"
                    ),
                ),
                ("description", models.TextField(blank=True, null=True)),
            ],
        ),
    ]
