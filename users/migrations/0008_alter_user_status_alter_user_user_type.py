# Generated by Django 4.1 on 2022-09-27 11:55

from django.db import migrations

import cores.models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0007_alter_usertestcount_table"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="status",
            field=cores.models.EnumField(
                default="active", enum=cores.models.UserStatus, max_length=10
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="user_type",
            field=cores.models.EnumField(
                default="normal", enum=cores.models.UserType, max_length=10
            ),
        ),
    ]
