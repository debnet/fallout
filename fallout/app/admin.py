# coding: utf-8
from django.contrib import admin
from .models import Ammo, Apparel, Character, Item, Weapon

admin.site.register(Ammo)
admin.site.register(Apparel)
admin.site.register(Character)
admin.site.register(Item)
admin.site.register(Weapon)
