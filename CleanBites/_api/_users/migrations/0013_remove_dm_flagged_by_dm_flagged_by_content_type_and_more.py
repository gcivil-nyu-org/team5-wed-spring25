# Generated by Django 4.2.20 on 2025-04-15 20:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("_users", "0012_moderator_deactivation_reason_moderator_is_activated"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="dm",
            name="flagged_by",
        ),
        migrations.AddField(
            model_name="dm",
            name="flagged_by_content_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="dm",
            name="flagged_by_object_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
