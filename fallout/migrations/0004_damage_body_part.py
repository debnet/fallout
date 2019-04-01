# Generated by Django 2.1.7 on 2019-04-01 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fallout', '0003_equipment_secondary'),
    ]

    operations = [
        migrations.AddField(
            model_name='damagehistory',
            name='body_part',
            field=models.CharField(blank=True, choices=[('torso', 'torse'), ('legs', 'jambes'), ('arms', 'bras'), ('head', 'tête'), ('eyes', 'yeux')], max_length=10, verbose_name='partie du corps'),
        ),
        migrations.AddField(
            model_name='effect',
            name='body_part',
            field=models.CharField(blank=True, choices=[('torso', 'torse'), ('legs', 'jambes'), ('arms', 'bras'), ('head', 'tête'), ('eyes', 'yeux')], max_length=10, verbose_name='partie du corps'),
        ),
        migrations.AddField(
            model_name='item',
            name='body_part',
            field=models.CharField(blank=True, choices=[('torso', 'torse'), ('legs', 'jambes'), ('arms', 'bras'), ('head', 'tête'), ('eyes', 'yeux')], max_length=10, verbose_name='partie du corps'),
        ),
    ]
