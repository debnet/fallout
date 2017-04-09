# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-09 00:08
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import rpg.fallout.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ActiveEffect',
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
                'verbose_name_plural': 'effets en cours',
                'verbose_name': 'effet en cours',
            },
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='nom')),
                ('start_game_date', models.DateTimeField(verbose_name='date de début')),
                ('current_game_date', models.DateTimeField(verbose_name='date courante')),
                ('radiation', models.PositiveSmallIntegerField(default=0, verbose_name='rads par heure')),
            ],
            options={
                'verbose_name_plural': 'campagnes',
                'verbose_name': 'campagne',
            },
        ),
        migrations.CreateModel(
            name='Character',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('strength', models.PositiveSmallIntegerField(default=1, verbose_name='force')),
                ('perception', models.PositiveSmallIntegerField(default=1, verbose_name='perception')),
                ('endurance', models.PositiveSmallIntegerField(default=1, verbose_name='endurance')),
                ('charisma', models.PositiveSmallIntegerField(default=1, verbose_name='charisme')),
                ('intelligence', models.PositiveSmallIntegerField(default=1, verbose_name='intelligence')),
                ('agility', models.PositiveSmallIntegerField(default=1, verbose_name='agilité')),
                ('luck', models.PositiveSmallIntegerField(default=1, verbose_name='chance')),
                ('max_health', models.PositiveSmallIntegerField(default=0, verbose_name='santé maximale')),
                ('max_action_points', models.PositiveSmallIntegerField(default=0, verbose_name="points d'action max.")),
                ('armor_class', models.SmallIntegerField(default=0, verbose_name='esquive')),
                ('carry_weight', models.SmallIntegerField(default=0, verbose_name='charge maximale')),
                ('melee_damage', models.SmallIntegerField(default=0, verbose_name='attaque en mélée')),
                ('sequence', models.SmallIntegerField(default=0, verbose_name='initiative')),
                ('healing_rate', models.SmallIntegerField(default=0, verbose_name='taux de regénération')),
                ('critical_chance', models.SmallIntegerField(default=0, verbose_name='chance de critique')),
                ('damage_threshold', models.SmallIntegerField(default=0, verbose_name='seuil de dégâts')),
                ('damage_resistance', models.FloatField(default=0.0, verbose_name='résistance aux dégâts')),
                ('normal_resistance', models.FloatField(default=0.0, verbose_name='résistance physique')),
                ('laser_resistance', models.FloatField(default=0.0, verbose_name='résistance au laser')),
                ('plasma_resistance', models.FloatField(default=0.0, verbose_name='résistance au plasma')),
                ('explosive_resistance', models.FloatField(default=0.0, verbose_name='résistance aux explosions')),
                ('fire_resistance', models.FloatField(default=0.0, verbose_name='résistance au feu')),
                ('gas_contact_resistance', models.FloatField(default=0.0, verbose_name='résistance au gaz (contact)')),
                ('gas_inhaled_resistance', models.FloatField(default=0.0, verbose_name='résistance au gaz (inhalé)')),
                ('electricity_resistance', models.FloatField(default=0.0, verbose_name="résistance à l'électricité")),
                ('poison_resistance', models.FloatField(default=0.0, verbose_name='résistance aux poisons')),
                ('radiation_resistance', models.FloatField(default=0.0, verbose_name='résistance aux radiations')),
                ('small_guns', models.SmallIntegerField(default=0, verbose_name='armes à feu légères')),
                ('big_guns', models.SmallIntegerField(default=0, verbose_name='armes à feu lourdes')),
                ('energy_weapons', models.SmallIntegerField(default=0, verbose_name='armes à énergie')),
                ('unarmed', models.SmallIntegerField(default=0, verbose_name='à mains nues')),
                ('melee_weapons', models.SmallIntegerField(default=0, verbose_name='armes de mélée')),
                ('throwing', models.SmallIntegerField(default=0, verbose_name='armes de lancer')),
                ('first_aid', models.SmallIntegerField(default=0, verbose_name='premiers secours')),
                ('doctor', models.SmallIntegerField(default=0, verbose_name='médecine')),
                ('chems', models.SmallIntegerField(default=0, verbose_name='chimie')),
                ('sneak', models.SmallIntegerField(default=0, verbose_name='discrétion')),
                ('lockpick', models.SmallIntegerField(default=0, verbose_name='crochetage')),
                ('steal', models.SmallIntegerField(default=0, verbose_name='pickpocket')),
                ('traps', models.SmallIntegerField(default=0, verbose_name='pièges')),
                ('science', models.SmallIntegerField(default=0, verbose_name='science')),
                ('repair', models.SmallIntegerField(default=0, verbose_name='réparation')),
                ('speech', models.SmallIntegerField(default=0, verbose_name='discours')),
                ('barter', models.SmallIntegerField(default=0, verbose_name='marchandage')),
                ('gambling', models.SmallIntegerField(default=0, verbose_name='hasard')),
                ('survival', models.SmallIntegerField(default=0, verbose_name='survie')),
                ('knowledge', models.SmallIntegerField(default=0, verbose_name='connaissance')),
                ('hit_points_per_level', models.SmallIntegerField(default=0, verbose_name='santé par niveau')),
                ('skill_points_per_level', models.SmallIntegerField(default=0, verbose_name='compétences par niveau')),
                ('perk_rate', models.SmallIntegerField(default=0, verbose_name='niveaux pour un talent')),
                ('name', models.CharField(max_length=200, verbose_name='nom')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='titre')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('image', models.ImageField(blank=True, upload_to='', verbose_name='image')),
                ('race', models.CharField(choices=[('human', 'humain'), ('ghoul', 'ghoule'), ('super_mutant', 'super-mutant'), ('deathclaw', 'écorcheur'), ('robot', 'robot'), ('animal', 'animal')], db_index=True, default='human', max_length=12, verbose_name='race')),
                ('level', models.PositiveSmallIntegerField(default=1, verbose_name='niveau')),
                ('is_player', models.BooleanField(db_index=True, default=False, verbose_name='joueur ?')),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='actif ?')),
                ('is_resting', models.BooleanField(default=False, verbose_name='au repos ?')),
                ('health', models.PositiveSmallIntegerField(default=0, verbose_name='santé')),
                ('action_points', models.PositiveSmallIntegerField(default=0, verbose_name="points d'action")),
                ('skill_points', models.PositiveSmallIntegerField(default=0, verbose_name='points de compétence')),
                ('perk_points', models.PositiveSmallIntegerField(default=0, verbose_name='points de talent')),
                ('experience', models.PositiveIntegerField(default=0, verbose_name='expérience')),
                ('karma', models.SmallIntegerField(default=0, verbose_name='karma')),
                ('irradiation', models.FloatField(default=0.0, verbose_name='irradiation')),
                ('dehydration', models.FloatField(default=0.0, verbose_name='soif')),
                ('hunger', models.FloatField(default=0.0, verbose_name='faim')),
                ('sleep', models.FloatField(default=0.0, verbose_name='sommeil')),
                ('regeneration', models.FloatField(default=0.0, verbose_name='regénération')),
                ('tag_skills', rpg.fallout.fields.MultipleChoiceField(blank=True, choices=[('small_guns', 'armes à feu légères'), ('big_guns', 'armes à feu lourdes'), ('energy_weapons', 'armes à énergie'), ('unarmed', 'à mains nues'), ('melee_weapons', 'armes de mélée'), ('throwing', 'armes de lancer'), ('first_aid', 'premiers secours'), ('doctor', 'médecine'), ('chems', 'chimie'), ('sneak', 'discrétion'), ('lockpick', 'crochetage'), ('steal', 'pickpocket'), ('traps', 'pièges'), ('science', 'science'), ('repair', 'réparation'), ('speech', 'discours'), ('barter', 'marchandage'), ('gambling', 'hasard'), ('survival', 'survie'), ('knowledge', 'connaissance')], max_length=200, verbose_name='spécialités')),
                ('campaign', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='characters', to='fallout.Campaign', verbose_name='campagne')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='characters', to=settings.AUTH_USER_MODEL, verbose_name='utilisateur')),
            ],
            options={
                'verbose_name_plural': 'personnages',
                'verbose_name': 'personnage',
            },
        ),
        migrations.CreateModel(
            name='Effect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('name', models.CharField(max_length=200, verbose_name='nom')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='titre')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('image', models.ImageField(blank=True, upload_to='', verbose_name='image')),
                ('chance', models.PositiveSmallIntegerField(default=100, verbose_name='chance')),
                ('duration', models.DurationField(blank=True, null=True, verbose_name='durée')),
                ('interval', models.DurationField(blank=True, null=True, verbose_name='intervalle')),
                ('damage_type', models.CharField(blank=True, choices=[('normal', 'dégâts normaux'), ('laser', 'dégâts de laser'), ('plasma', 'dégâts de plasma'), ('explosive', 'dégâts explosifs'), ('fire', 'dégâts de feu'), ('gas_contact', 'dégâts de gaz (contact)'), ('gas_inhaled', 'dégâts de gaz (inhalé)'), ('electricity', "dégâts d'électricité"), ('poison', 'dégâts de poison'), ('radiation', 'dégâts de radiations'), ('heal', 'soins')], max_length=10, verbose_name='type de dégâts')),
                ('damage_dice_count', models.PositiveSmallIntegerField(default=0, verbose_name='nombre de dés')),
                ('damage_dice_value', models.PositiveSmallIntegerField(default=0, verbose_name='valeur de dé')),
                ('damage_bonus', models.PositiveSmallIntegerField(default=0, verbose_name='bonus au dé')),
            ],
            options={
                'verbose_name_plural': 'effets',
                'verbose_name': 'effet',
            },
        ),
        migrations.CreateModel(
            name='EffectModifier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stats', models.CharField(choices=[('S.P.E.C.I.A.L.', (('strength', 'force'), ('perception', 'perception'), ('endurance', 'endurance'), ('charisma', 'charisme'), ('intelligence', 'intelligence'), ('agility', 'agilité'), ('luck', 'chance'))), ('Compétences', (('small_guns', 'armes à feu légères'), ('big_guns', 'armes à feu lourdes'), ('energy_weapons', 'armes à énergie'), ('unarmed', 'à mains nues'), ('melee_weapons', 'armes de mélée'), ('throwing', 'armes de lancer'), ('first_aid', 'premiers secours'), ('doctor', 'médecine'), ('chems', 'chimie'), ('sneak', 'discrétion'), ('lockpick', 'crochetage'), ('steal', 'pickpocket'), ('traps', 'pièges'), ('science', 'science'), ('repair', 'réparation'), ('speech', 'discours'), ('barter', 'marchandage'), ('gambling', 'hasard'), ('survival', 'survie'), ('knowledge', 'connaissance'))), ['Statistiques générales', (('health', 'santé'), ('action_points', "points d'action"), ('skill_points', 'points de compétence'), ('perk_points', 'points de talent'), ('experience', 'expérience'), ('karma', 'karma'), ('irradiation', 'irradiation'), ('dehydration', 'soif'), ('hunger', 'faim'), ('sleep', 'sommeil'))], ('Statistiques secondaires', (('max_health', 'santé maximale'), ('max_action_points', "points d'action max."), ('armor_class', 'esquive'), ('carry_weight', 'charge maximale'), ('melee_damage', 'attaque en mélée'), ('sequence', 'initiative'), ('healing_rate', 'taux de regénération'), ('critical_chance', 'chance de critique'), ('damage_threshold', 'seuil de dégâts'), ('damage_resistance', 'résistance aux dégâts'))), ('Résistances', (('normal_resistance', 'résistance aux dégâts'), ('laser_resistance', 'résistance au laser'), ('plasma_resistance', 'résistance au plasma'), ('explosive_resistance', 'résistance aux explosions'), ('fire_resistance', 'résistance au feu'), ('gas_contact_resistance', 'résistance au gaz (contact)'), ('gas_inhaled_resistance', 'résistance au gaz (inhalé)'), ('electricity_resistance', "résistance à l'électricité"), ('poison_resistance', 'résistance aux poisons'), ('radiation_resistance', 'résistance aux radiations'))), ('Statistiques de niveau', (('hit_points_per_level', 'santé par niveau'), ('skill_points_per_level', 'compétences par niveau'), ('perk_rate', 'niveaux pour un talent')))], max_length=20, verbose_name='statistique')),
                ('value', models.SmallIntegerField(default=0, verbose_name='valeur')),
                ('effect', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modifiers', to='fallout.Effect', verbose_name='effet')),
            ],
            options={
                'verbose_name_plural': "modificateurs d'effets",
                'verbose_name': "modificateur d'effet",
            },
        ),
        migrations.CreateModel(
            name='Equipment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('slot', models.CharField(blank=True, choices=[('weapon', 'arme'), ('ammo', 'munition'), ('armor', 'armure'), ('implant', 'implant')], max_length=7, verbose_name='emplacement')),
                ('count', models.PositiveIntegerField(default=1, verbose_name='nombre')),
                ('clip_count', models.PositiveSmallIntegerField(default=0, verbose_name='munitions')),
                ('condition', models.FloatField(default=1.0, verbose_name='état')),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='equipments', to='fallout.Character', verbose_name='personnage')),
            ],
            options={
                'verbose_name_plural': 'équipements',
                'verbose_name': 'équipement',
            },
        ),
        migrations.CreateModel(
            name='FightHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('game_date', models.DateTimeField(blank=True, null=True, verbose_name='date en jeu')),
                ('burst', models.BooleanField(default=False, verbose_name='tir en rafale ?')),
                ('range', models.PositiveSmallIntegerField(default=0, verbose_name='distance')),
                ('body_part', models.CharField(choices=[('torso', 'torse'), ('legs', 'jambes'), ('arms', 'bras'), ('head', 'tête'), ('eyes', 'yeux')], max_length=5, verbose_name='partie du corps')),
                ('hit_modifier', models.SmallIntegerField(default=0, verbose_name='modif. de précision')),
                ('hit_chance', models.SmallIntegerField(default=0, verbose_name='précision')),
                ('hit_roll', models.PositiveSmallIntegerField(default=0, verbose_name='jet de précision')),
                ('hit_success', models.BooleanField(default=False, verbose_name='touché ?')),
                ('hit_critical', models.BooleanField(default=False, verbose_name='critique ?')),
                ('base_damage', models.PositiveSmallIntegerField(default=0, verbose_name='dégâts de base')),
                ('damage', models.PositiveSmallIntegerField(default=0, verbose_name='dégâts réels')),
                ('status', models.CharField(blank=True, choices=[('hit_succeed', 'cible touchée'), ('hit_failed', 'cible manquée'), ('no_more_ammo', 'munitions insuffisantes'), ('target_dead', 'cible inconsciente'), ('weapon_broken', 'arme défectueuse')], max_length=15, verbose_name='status')),
                ('attacker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Character', verbose_name='attaquant')),
            ],
            options={
                'verbose_name_plural': 'historiques de combats',
                'verbose_name': 'historique de combat',
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('name', models.CharField(max_length=200, verbose_name='nom')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='titre')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('image', models.ImageField(blank=True, upload_to='', verbose_name='image')),
                ('type', models.CharField(choices=[('weapon', 'arme'), ('ammo', 'munition'), ('armor', 'armure'), ('implant', 'implant'), ('food', 'nourriture'), ('chem', 'drogue'), ('misc', 'autre')], max_length=7, verbose_name='type')),
                ('value', models.PositiveIntegerField(default=0, verbose_name='valeur')),
                ('weight', models.FloatField(default=0.0, verbose_name='poids')),
                ('is_quest', models.BooleanField(default=False, verbose_name='quête ?')),
                ('is_melee', models.BooleanField(default=False, verbose_name='arme de mêlée ?')),
                ('is_throwable', models.BooleanField(default=False, verbose_name='jetable ?')),
                ('damage_type', models.CharField(blank=True, choices=[('normal', 'dégâts normaux'), ('laser', 'dégâts de laser'), ('plasma', 'dégâts de plasma'), ('explosive', 'dégâts explosifs'), ('fire', 'dégâts de feu'), ('gas_contact', 'dégâts de gaz (contact)'), ('gas_inhaled', 'dégâts de gaz (inhalé)'), ('electricity', "dégâts d'électricité"), ('poison', 'dégâts de poison'), ('radiation', 'dégâts de radiations'), ('heal', 'soins')], max_length=10, verbose_name='type de dégâts')),
                ('damage_dice_count', models.PositiveSmallIntegerField(default=0, verbose_name='nombre de dés')),
                ('damage_dice_value', models.PositiveSmallIntegerField(default=0, verbose_name='valeur de dé')),
                ('damage_bonus', models.PositiveSmallIntegerField(default=0, verbose_name='bonus de dégâts')),
                ('range', models.PositiveSmallIntegerField(default=1, verbose_name='portée')),
                ('clip_size', models.PositiveSmallIntegerField(default=0, verbose_name='taille du chargeur')),
                ('ap_cost_reload', models.PositiveSmallIntegerField(default=0, verbose_name='coût PA recharge')),
                ('ap_cost_normal', models.PositiveSmallIntegerField(default=0, verbose_name='coût PA normal')),
                ('ap_cost_target', models.PositiveSmallIntegerField(default=0, verbose_name='coût PA ciblé')),
                ('ap_cost_burst', models.PositiveSmallIntegerField(default=0, verbose_name='coût PA rafale')),
                ('burst_count', models.PositiveSmallIntegerField(default=0, verbose_name='munitions en rafale')),
                ('min_strength', models.PositiveSmallIntegerField(default=0, verbose_name='force minimum')),
                ('skill', models.CharField(blank=True, choices=[('small_guns', 'armes à feu légères'), ('big_guns', 'armes à feu lourdes'), ('energy_weapons', 'armes à énergie'), ('unarmed', 'à mains nues'), ('melee_weapons', 'armes de mélée'), ('throwing', 'armes de lancer'), ('first_aid', 'premiers secours'), ('doctor', 'médecine'), ('chems', 'chimie'), ('sneak', 'discrétion'), ('lockpick', 'crochetage'), ('steal', 'pickpocket'), ('traps', 'pièges'), ('science', 'science'), ('repair', 'réparation'), ('speech', 'discours'), ('barter', 'marchandage'), ('gambling', 'hasard'), ('survival', 'survie'), ('knowledge', 'connaissance')], max_length=10, verbose_name='compétence')),
                ('hit_chance_modifier', models.SmallIntegerField(default=0, verbose_name='modif. de précision')),
                ('armor_class_modifier', models.SmallIntegerField(default=0, verbose_name="modif. d'esquive")),
                ('resistance_modifier', models.FloatField(default=1.0, verbose_name='modif. de resistance')),
                ('range_modifier', models.FloatField(default=1.0, verbose_name='modif. de portée')),
                ('damage_modifier', models.FloatField(default=1.0, verbose_name='modif. de dégâts')),
                ('critical_modifier', models.FloatField(default=1.0, verbose_name='modif. de coup critique')),
                ('condition_modifier', models.FloatField(default=0.0, verbose_name='modif. de condition')),
                ('normal_threshold', models.PositiveSmallIntegerField(default=0, verbose_name='seuil normal')),
                ('normal_resistance', models.FloatField(default=0.0, verbose_name='résistance normal')),
                ('laser_threshold', models.PositiveSmallIntegerField(default=0, verbose_name='seuil laser')),
                ('laser_resistance', models.FloatField(default=0.0, verbose_name='résistance laser')),
                ('plasma_threshold', models.PositiveSmallIntegerField(default=0, verbose_name='seuil plasma')),
                ('plasma_resistance', models.FloatField(default=0.0, verbose_name='résistance plasma')),
                ('explosive_threshold', models.PositiveSmallIntegerField(default=0, verbose_name='seuil explosifs')),
                ('explosive_resistance', models.FloatField(default=0.0, verbose_name='résistance explosifs')),
                ('fire_threshold', models.PositiveSmallIntegerField(default=0, verbose_name='seuil feu')),
                ('fire_resistance', models.FloatField(default=0.0, verbose_name='résistance feu')),
                ('ammunition', models.ManyToManyField(blank=True, to='fallout.Item', verbose_name='type de munition')),
                ('effects', models.ManyToManyField(blank=True, related_name='_item_effects_+', to='fallout.Effect', verbose_name='effets')),
            ],
            options={
                'verbose_name_plural': 'objets',
                'verbose_name': 'objet',
            },
        ),
        migrations.CreateModel(
            name='ItemModifier',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stats', models.CharField(choices=[('S.P.E.C.I.A.L.', (('strength', 'force'), ('perception', 'perception'), ('endurance', 'endurance'), ('charisma', 'charisme'), ('intelligence', 'intelligence'), ('agility', 'agilité'), ('luck', 'chance'))), ('Compétences', (('small_guns', 'armes à feu légères'), ('big_guns', 'armes à feu lourdes'), ('energy_weapons', 'armes à énergie'), ('unarmed', 'à mains nues'), ('melee_weapons', 'armes de mélée'), ('throwing', 'armes de lancer'), ('first_aid', 'premiers secours'), ('doctor', 'médecine'), ('chems', 'chimie'), ('sneak', 'discrétion'), ('lockpick', 'crochetage'), ('steal', 'pickpocket'), ('traps', 'pièges'), ('science', 'science'), ('repair', 'réparation'), ('speech', 'discours'), ('barter', 'marchandage'), ('gambling', 'hasard'), ('survival', 'survie'), ('knowledge', 'connaissance'))), ['Statistiques générales', (('health', 'santé'), ('action_points', "points d'action"), ('skill_points', 'points de compétence'), ('perk_points', 'points de talent'), ('experience', 'expérience'), ('karma', 'karma'), ('irradiation', 'irradiation'), ('dehydration', 'soif'), ('hunger', 'faim'), ('sleep', 'sommeil'))], ('Statistiques secondaires', (('max_health', 'santé maximale'), ('max_action_points', "points d'action max."), ('armor_class', 'esquive'), ('carry_weight', 'charge maximale'), ('melee_damage', 'attaque en mélée'), ('sequence', 'initiative'), ('healing_rate', 'taux de regénération'), ('critical_chance', 'chance de critique'), ('damage_threshold', 'seuil de dégâts'), ('damage_resistance', 'résistance aux dégâts'))), ('Résistances', (('normal_resistance', 'résistance aux dégâts'), ('laser_resistance', 'résistance au laser'), ('plasma_resistance', 'résistance au plasma'), ('explosive_resistance', 'résistance aux explosions'), ('fire_resistance', 'résistance au feu'), ('gas_contact_resistance', 'résistance au gaz (contact)'), ('gas_inhaled_resistance', 'résistance au gaz (inhalé)'), ('electricity_resistance', "résistance à l'électricité"), ('poison_resistance', 'résistance aux poisons'), ('radiation_resistance', 'résistance aux radiations'))), ('Statistiques de niveau', (('hit_points_per_level', 'santé par niveau'), ('skill_points_per_level', 'compétences par niveau'), ('perk_rate', 'niveaux pour un talent')))], max_length=20, verbose_name='statistique')),
                ('value', models.SmallIntegerField(default=0, verbose_name='valeur')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='modifiers', to='fallout.Item', verbose_name='objet')),
            ],
            options={
                'verbose_name_plural': "modificateurs d'objets",
                'verbose_name': "modificateur d'objet",
            },
        ),
        migrations.CreateModel(
            name='Loot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveIntegerField(default=1, verbose_name='nombre')),
                ('condition', models.FloatField(default=1.0, verbose_name='état')),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loots', to='fallout.Campaign', verbose_name='campagne')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='loots', to='fallout.Item', verbose_name='objet')),
            ],
            options={
                'verbose_name_plural': 'butins',
                'verbose_name': 'butin',
            },
        ),
        migrations.CreateModel(
            name='LootTemplate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('name', models.CharField(max_length=200, verbose_name='nom')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='titre')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('image', models.ImageField(blank=True, upload_to='', verbose_name='image')),
            ],
            options={
                'verbose_name_plural': 'modèles de butins',
                'verbose_name': 'modèle de butin',
            },
        ),
        migrations.CreateModel(
            name='LootTemplateItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='UUID')),
                ('creation_date', models.DateTimeField(auto_now_add=True, verbose_name='date de création')),
                ('modification_date', models.DateTimeField(auto_now=True, verbose_name='date de modification')),
                ('chance', models.PositiveSmallIntegerField(default=100, verbose_name='chance')),
                ('min_count', models.PositiveIntegerField(default=1, verbose_name='nombre min.')),
                ('max_count', models.PositiveIntegerField(default=1, null=True, verbose_name='nombre max.')),
                ('min_condition', models.FloatField(default=1.0, verbose_name='état min.')),
                ('max_condition', models.FloatField(default=1.0, verbose_name='état max.')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Item', verbose_name='objet')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='fallout.LootTemplate', verbose_name='modèle')),
            ],
            options={
                'verbose_name_plural': 'objets de butins',
                'verbose_name': 'objet de butin',
            },
        ),
        migrations.CreateModel(
            name='RollHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True, verbose_name='date')),
                ('game_date', models.DateTimeField(blank=True, null=True, verbose_name='date en jeu')),
                ('stats', models.CharField(blank=True, choices=[('S.P.E.C.I.A.L.', (('strength', 'force'), ('perception', 'perception'), ('endurance', 'endurance'), ('charisma', 'charisme'), ('intelligence', 'intelligence'), ('agility', 'agilité'), ('luck', 'chance'))), ('Compétences', (('small_guns', 'armes à feu légères'), ('big_guns', 'armes à feu lourdes'), ('energy_weapons', 'armes à énergie'), ('unarmed', 'à mains nues'), ('melee_weapons', 'armes de mélée'), ('throwing', 'armes de lancer'), ('first_aid', 'premiers secours'), ('doctor', 'médecine'), ('chems', 'chimie'), ('sneak', 'discrétion'), ('lockpick', 'crochetage'), ('steal', 'pickpocket'), ('traps', 'pièges'), ('science', 'science'), ('repair', 'réparation'), ('speech', 'discours'), ('barter', 'marchandage'), ('gambling', 'hasard'), ('survival', 'survie'), ('knowledge', 'connaissance')))], max_length=10, verbose_name='statistique')),
                ('value', models.PositiveSmallIntegerField(default=0, verbose_name='valeur')),
                ('modifier', models.SmallIntegerField(default=0, verbose_name='modificateur')),
                ('roll', models.PositiveIntegerField(default=0, verbose_name='jet')),
                ('success', models.BooleanField(default=False, verbose_name='succès ?')),
                ('critical', models.BooleanField(default=False, verbose_name='critique ?')),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Character', verbose_name='personnage')),
            ],
            options={
                'verbose_name_plural': 'historiques de jets',
                'verbose_name': 'historique de jet',
            },
        ),
        migrations.AddField(
            model_name='fighthistory',
            name='attacker_ammo',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Item', verbose_name="munitions de l'attaquant"),
        ),
        migrations.AddField(
            model_name='fighthistory',
            name='attacker_weapon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Item', verbose_name="arme de l'attaquant"),
        ),
        migrations.AddField(
            model_name='fighthistory',
            name='defender',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Character', verbose_name='défenseur'),
        ),
        migrations.AddField(
            model_name='fighthistory',
            name='defender_armor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Item', verbose_name='protection du défenseur'),
        ),
        migrations.AddField(
            model_name='equipment',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='fallout.Item', verbose_name='objet'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='active_effects',
            field=models.ManyToManyField(blank=True, related_name='_campaign_active_effects_+', to='fallout.Effect', verbose_name='effets actifs'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='current_character',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='fallout.Character', verbose_name='personnage actif'),
        ),
        migrations.AddField(
            model_name='activeeffect',
            name='character',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='active_effects', to='fallout.Character', verbose_name='personnage'),
        ),
        migrations.AddField(
            model_name='activeeffect',
            name='effect',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='active_effects', to='fallout.Effect', verbose_name='effet'),
        ),
    ]
