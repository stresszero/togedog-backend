# Generated by Django 4.1 on 2022-09-25 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageSaveTest",
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
                ("message", models.CharField(max_length=50)),
                ("sender_nickname", models.CharField(max_length=10)),
                ("sender_id", models.IntegerField()),
                ("room_id", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "message_save_test",
            },
        ),
    ]
