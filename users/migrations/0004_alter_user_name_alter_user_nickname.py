# Generated by Django 4.1 on 2022-09-22 04:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_alter_user_thumbnail_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="name",
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name="user",
            name="nickname",
            field=models.CharField(max_length=30),
        ),
    ]