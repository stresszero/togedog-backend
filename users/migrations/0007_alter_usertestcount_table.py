# Generated by Django 4.1 on 2022-09-26 10:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_usertestcount"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="usertestcount",
            table="user_test_count",
        ),
    ]
