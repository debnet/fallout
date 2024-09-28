# Generated by Django 5.1.1 on 2024-09-14 19:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fallout", "0002_money"),
    ]

    operations = [
        migrations.AddField(
            model_name="fighthistory",
            name="experience",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="expérience"),
        ),
        migrations.AddField(
            model_name="fighthistory",
            name="level_up",
            field=models.BooleanField(default=False, verbose_name="niveau+ ?"),
        ),
        migrations.AddField(
            model_name="rollhistory",
            name="experience",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="expérience"),
        ),
        migrations.AddField(
            model_name="rollhistory",
            name="level_up",
            field=models.BooleanField(default=False, verbose_name="niveau+ ?"),
        ),
    ]
