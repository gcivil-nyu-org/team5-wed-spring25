# Generated by Django 4.2.20 on 2025-04-14 16:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("_users", "0010_customerdeactivated_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="CustomerDeactivated",
        ),
        migrations.AddField(
            model_name="customer",
            name="deactivation_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="customer",
            name="is_activated",
            field=models.BooleanField(default=True),
        ),
    ]
