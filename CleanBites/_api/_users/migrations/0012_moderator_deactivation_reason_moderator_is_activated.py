# Generated by Django 4.2.20 on 2025-04-14 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("_users", "0011_delete_customerdeactivated_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="moderator",
            name="deactivation_reason",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="moderator",
            name="is_activated",
            field=models.BooleanField(default=True),
        ),
    ]
