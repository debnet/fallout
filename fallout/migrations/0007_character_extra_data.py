# Generated by Django 2.2.4 on 2019-08-09 17:25

import common.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fallout', '0006_damage_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='extra_data',
            field=common.fields.JsonField(blank=True, null=True, verbose_name='données complémentaires'),
        ),
    ]
