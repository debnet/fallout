# Generated by Django 3.0.6 on 2020-05-29 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fallout', '0010_extends_damage'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='view_npc',
            field=models.BooleanField(default=False, verbose_name='voir les personnages non-joueurs'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='view_pc',
            field=models.BooleanField(default=False, verbose_name='voir les personnages joueurs'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='view_rolls',
            field=models.BooleanField(default=False, verbose_name='voir les jets lancés'),
        ),
    ]
