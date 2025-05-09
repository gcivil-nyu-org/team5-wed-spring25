# Generated by Django 4.2.20 on 2025-04-22 18:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("_users", "0014_customer_deactivated_until"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="blocked_customers",
            field=models.ManyToManyField(
                blank=True, related_name="blocked_by", to="_users.customer"
            ),
        ),
    ]
