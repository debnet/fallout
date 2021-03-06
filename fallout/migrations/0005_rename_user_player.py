# Generated by Django 2.1.7 on 2019-04-01 12:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fallout', '0004_damage_body_part'),
    ]

    operations = [
        migrations.RenameField(
            model_name='character',
            old_name='user',
            new_name='player',
        ),
        migrations.AlterField(
            model_name='character',
            name='player',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='characters', to=settings.AUTH_USER_MODEL, verbose_name='joueur'),
        ),
    ]
