# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-12 16:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('fallout', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel('activeeffect', 'charactereffect'),
        migrations.AlterModelOptions(
            name='charactereffect',
            options={'verbose_name': 'effet de personnage', 'verbose_name_plural': 'effets de personnage'},
        ),
        migrations.AlterField(
            model_name='charactereffect',
            name='effect',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Effect', verbose_name='effet'),
        ),
        migrations.RemoveField(
            model_name='campaign',
            name='active_effects',
        ),
        migrations.AddField(
            model_name='effect',
            name='damage_chance',
            field=models.PositiveSmallIntegerField(default=100, verbose_name='chance'),
        ),
        migrations.CreateModel(
            name='CampaignEffect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('start_date', models.DateTimeField(blank=True, null=True, verbose_name="date d'effet")),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name="date d'arrêt")),
                ('next_date', models.DateTimeField(blank=True, null=True, verbose_name='date suivante')),
            ],
            options={
                'verbose_name': 'effet de campagne',
                'verbose_name_plural': 'effets de campagne',
            },
        ),
        migrations.AddField(
            model_name='campaigneffect',
            name='campaign',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='active_effects', to='fallout.Campaign', verbose_name='campagne'),
        ),
        migrations.AddField(
            model_name='campaigneffect',
            name='effect',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Effect', verbose_name='effet'),
        ),
    ]
