# Generated by Django 4.1 on 2022-09-19 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comments", "0006_commentreport"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="content",
            field=models.CharField(blank=True, max_length=300),
        ),
    ]
