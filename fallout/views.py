# coding: utf-8
from common.utils import ajax_request, render_to, to_object
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from rest_framework.authtoken.models import Token

from fallout.enums import *  # noqa
from fallout.models import *  # noqa
from fallout.forms import QuickCreateCharacterForm


@login_required
def view_index(request):
    """
    Page d'accueil
    """
    characters = Character.objects.filter(player=request.user).values_list("id", flat=True)
    if len(characters) == 1 and not request.user.is_superuser:
        return view_character(request, characters[0])
    return view_campaign(request, 0)


def view_token(request, token):
    """
    Accès par jeton d'authentification
    """
    token = Token.objects.select_related("user").filter(key=token).first()
    if token:
        login(request, token.user)
    campaign_id, character_id = request.GET.get("campaign"), request.GET.get("character")
    if campaign_id:
        return redirect("fallout:campaign", campaign_id)
    elif character_id:
        return redirect("fallout:character", character_id)
    return redirect("fallout:index")


@login_required
@render_to("fallout/campaign/dashboard.html")
def view_dashboard(request, campaign_id):
    """
    Vue générale
    """
    campaigns = Campaign.objects.annotate(
        pcs=Count(
            "characters",
            filter=Q(characters__is_player=True, characters__is_active=True),
        ),
        npcs=Count(
            "characters",
            filter=Q(characters__is_player=False, characters__is_active=True),
        ),
    ).select_related("current_character")
    if not request.user.is_superuser:
        campaigns = campaigns.filter(Q(characters__player=request.user) | Q(game_master=request.user))
    campaign = campaigns.filter(id=campaign_id).first()
    if campaign_id and not campaign:
        raise Http404()

    characters = Character.objects.select_related("player", "statistics", "campaign__current_character").filter(
        campaign=campaign, is_active=True
    )
    if not request.user.is_superuser:
        characters = characters.filter(
            Q(player=request.user)
            | Q(campaign__game_master=request.user)
            | Q(is_player=True, campaign__view_pc=True)
            | Q(is_player=False, campaign__view_npc=True)
        )

    authorized = request.user and (
        request.user.is_superuser or (campaign and campaign.game_master_id == request.user.id)
    )

    try:
        if request.method == "POST" and authorized:
            data = request.POST
            if "roll" in data:
                stats = data.get("roll")
                modifier = int(data.get("modifier") or 0)
                modifier = int(modifier / 10) if stats in LIST_SPECIALS else modifier
                character = characters.filter(id=data.get("character")).first()
                result = character.roll(stats=stats, modifier=modifier)
                messages.add_message(
                    request,
                    result.message_level,
                    _("<strong>{pre_label}</strong> {label}").format(
                        pre_label=result.pre_label, label=result.long_label
                    ),
                )
            elif "rest" in data:
                characters.filter(id=data.get("rest")).update(is_resting=Q(is_resting=False))
    except ValidationError as error:
        for field, errors in error.message_dict.items():
            for error in errors if isinstance(errors, list) else [errors]:
                messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))

    return {
        "page": "dashboard",
        "authorized": authorized,
        # Lists
        "campaigns": campaigns.distinct().order_by("name", "title"),
        "characters": characters.order_by("-is_player", "name", "title"),
        # Campaign
        "campaign": campaign,
    }


@login_required
@render_to("fallout/campaign/campaign.html")
def view_campaign(request, campaign_id):
    """
    Vue principale des campagnes
    """
    campaigns = Campaign.objects.annotate(
        pcs=Count(
            "characters",
            filter=Q(characters__is_player=True, characters__is_active=True),
        ),
        npcs=Count(
            "characters",
            filter=Q(characters__is_player=False, characters__is_active=True),
        ),
    ).select_related("current_character")
    if not request.user.is_superuser:
        campaigns = campaigns.filter(Q(characters__player=request.user) | Q(game_master=request.user))
    campaign = campaigns.filter(id=campaign_id).first()
    if campaign_id and not campaign:
        raise Http404()

    characters = Character.objects.select_related("player", "statistics", "campaign__current_character").filter(
        campaign=campaign, is_active=True
    )
    if not request.user.is_superuser:
        characters = characters.filter(
            Q(player=request.user)
            | Q(campaign__game_master=request.user)
            | Q(is_player=True, campaign__view_pc=True)
            | Q(is_player=False, campaign__view_npc=True)
        )
    loots = Loot.objects.select_related("item").filter(campaign=campaign).order_by("item__name")

    authorized = request.user and (
        request.user.is_superuser or (campaign and campaign.game_master_id == request.user.id)
    )

    try:
        if request.method == "POST" and authorized:
            data = request.POST
            type = data.get("type")
            method = data.get("method")
            if type == "money":
                character = int(data.get("character-id") or 0)
                money = int(data.get("money") or 0)
                if character:
                    Character.objects.filter(id=character).update(money=F("money") + money)
                else:
                    campaign.money += money
                    campaign.save(update_fields=("money",))
            elif type == "loot":
                if method == "open":
                    loot_id, loot_name = data.get("loot-id"), data.get("loot-name")
                    character_id = data.get("character-id") or None
                    filter = dict(pk=loot_id) if loot_id else dict(name__icontains=loot_name)
                    LootTemplate.objects.filter(**filter).first().create(campaign, character_id)
                elif method == "add":
                    item_id, item_name = data.get("item-id"), data.get("item-name")
                    quantity = int(data.get("quantity") or 1)
                    condition = int(data.get("condition") or 100) / 100.0
                    filter = dict(pk=item_id) if item_id else dict(name__icontains=item_name)
                    item = Item.objects.filter(**filter).first()
                    Loot.create(
                        campaign=campaign,
                        item=item,
                        quantity=quantity,
                        condition=condition,
                    )
                elif method == "clear":
                    Loot.objects.filter(campaign=campaign).delete()
                elif method.startswith("delete"):
                    method, loot_id = method.split("-")
                    quantity = int(data.get(f"quantity-{loot_id}") or 0)
                    if quantity:
                        loot = Loot.objects.filter(pk=loot_id).first()
                        loot.quantity -= quantity
                        loot.save()
                elif method.startswith("take"):
                    method, loot_id = method.split("-")
                    character = int(data.get("character-id") or 0)
                    quantity = int(data.get(f"quantity-{loot_id}") or 0)
                    is_action = bool(data.get("is_action"))
                    if loot_id and character and quantity:
                        loot = Loot.objects.filter(pk=loot_id).first()
                        loot.take(character, quantity, is_action=is_action)
                    elif money := min(int(data.get("money") or 0), campaign.money_loot):
                        if character:
                            Character.objects.filter(id=character).update(money=F("money") + money)
                        else:
                            campaign.money += money
                        campaign.money_loot -= money
                        campaign.save(update_fields=("money", "money_loot"))
            elif type == "damage":
                group, damage_type, body_part, min_damage, max_damage, raw_damage = (
                    data.get("group"),
                    data.get("damage_type"),
                    data.get("body_part"),
                    int(data.get("min_damage")),
                    int(data.get("max_damage")),
                    int(data.get("raw_damage")),
                )
                filter = dict(is_player=(group == "pj")) if group else dict()
                for character in characters.filter(is_active=True, **filter):
                    result = character.damage(raw_damage, min_damage, max_damage, damage_type, body_part)
                    messages.add_message(
                        request,
                        result.message_level,
                        _("<strong>{pre_label}</strong> {label}").format(
                            pre_label=result.pre_label, label=result.label
                        ),
                    )
            elif type == "effect":
                effect_id, effect_name = data.get("effect-id"), data.get("effect-name")
                if method == "add":
                    filter = dict(pk=effect_id) if effect_id else dict(name__icontains=effect_name)
                    effect = Effect.objects.filter(**filter).first().affect(campaign, force=True)
                    for damage in getattr(effect, "damages", []):
                        messages.add_message(
                            request,
                            damage.message_level,
                            _("<strong>{pre_label}</strong> {label}").format(
                                pre_label=damage.pre_label, label=damage.label
                            ),
                        )
                elif method == "remove":
                    scope = data.get("scope")
                    if scope == "character":
                        CharacterEffect.objects.filter(pk=effect_id).delete()
                    elif scope == "campaign":
                        CampaignEffect.objects.filter(pk=effect_id).delete()
            elif type == "radiation":
                if method == "set":
                    radiation = int(data.get("radiation") or 0)
                    campaign.radiation = radiation
                    campaign.save()
            elif type == "time":
                if method == "add":
                    hours, minutes, resting = (
                        int(data.get("hours") or 0),
                        int(data.get("minutes") or 0),
                        "resting" in data,
                    )
                    character, damages = campaign.next_turn(
                        seconds=hours * 3600 + minutes * 60, resting=resting, reset=True
                    )
                    for damage in damages:
                        messages.add_message(
                            request,
                            damage.message_level,
                            _("<strong>{pre_label}</strong> {label}").format(
                                pre_label=damage.pre_label, label=damage.label
                            ),
                        )
            elif type == "roll":
                group, stats, modifier, xp = (
                    data.get("group"),
                    data.get("stats"),
                    int(data.get("modifier") or 0),
                    "xp" in data,
                )
                filter = dict(is_player=(group == "pj")) if group else dict()
                for character in characters.filter(is_active=True, **filter):
                    result = character.roll(stats=stats, modifier=modifier, xp=xp)
                    messages.add_message(
                        request,
                        result.message_level,
                        _("<strong>{pre_label}</strong> {label}").format(
                            pre_label=result.pre_label, label=result.long_label
                        ),
                    )
            elif type == "gain":
                group, experience = (
                    data.get("group"),
                    int(data.get("experience") or 0),
                )
                filter = dict(is_player=(group == "pj")) if group else dict()
                for character in characters.filter(is_active=True, **filter):
                    old_level = character.level
                    level, required_experience = character.add_experience(experience)
                    if level != old_level:
                        messages.info(
                            request,
                            _(
                                "<strong>{character}</strong> vient de passer au niveau "
                                "<strong>{level}</strong> et a besoin de <strong>{experience}</strong> "
                                "points d'expérience pour passer au niveau suivant."
                            ).format(
                                character=character,
                                level=level,
                                experience=required_experience,
                            ),
                        )
                    else:
                        messages.success(
                            request,
                            _(
                                "<strong>{character}</strong> a encore besoin de <strong>{experience}</strong> "
                                "points d'expérience pour passer au niveau suivant."
                            ).format(character=character, experience=required_experience),
                        )
            elif type == "npc":
                name, number, character_id, campaign_id = (
                    data.get("name"),
                    int(data.get("number") or 1),
                    int(data.get("character-id") or 0),
                    int(data.get("campaign-id")),
                )
                character = Character.objects.filter(pk=character_id).first()
                for i in range(number):
                    if not character:
                        if not name:
                            continue
                        character = Character(name=name, has_stats=False, has_needs=False)
                        character.randomize_special(save=False)
                        character.generate_stats(save=False)
                    character.duplicate(campaign=campaign, name=name if number == 1 else f"{name} {i+1}")
                    if number > 1:
                        character = Character.objects.filter(pk=character_id).first()
    except ValidationError as error:
        for field, errors in error.message_dict.items():
            for error in errors if isinstance(errors, list) else [errors]:
                messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))
    except Exception as error:
        messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))

    all_items = Item.objects.order_by("type", "name").only("id", "name", "type", "title").to_dict(display=True)
    all_effects = Effect.objects.filter(character__isnull=True).order_by("name").only("id", "name", "title").to_dict()
    all_loots = LootTemplate.objects.order_by("name").only("id", "name", "title").to_dict()
    all_npcs = (
        Character.objects.filter(campaign__isnull=True, is_player=False)
        .order_by("name")
        .only("id", "name", "title", "level")
        .to_dict()
    )

    return {
        "page": "campaign",
        "authorized": authorized,
        # Lists
        "campaigns": campaigns.distinct().order_by("name", "title"),
        "characters": characters.order_by("-is_player", "name", "title"),
        # Campaign
        "campaign": campaign,
        "loots": loots,
        # Enums
        "stats": ROLL_STATS,
        "body_parts": BODY_PARTS,
        "damage_types": DAMAGES_TYPES,
        # Lists
        "all_items": all_items,
        "all_effects": all_effects,
        "all_loots": all_loots,
        "all_npcs": all_npcs,
    }


@login_required
@render_to("fallout/character/character.html")
def view_character(request, character_id):
    """
    Vue principale des personnages
    """
    campaigns = Campaign.objects.annotate(
        pcs=Count(
            "characters",
            filter=Q(characters__is_player=True, characters__is_active=True),
        ),
        npcs=Count(
            "characters",
            filter=Q(characters__is_player=False, characters__is_active=True),
        ),
    ).select_related("current_character")
    if not request.user.is_superuser:
        campaigns = campaigns.filter(Q(characters__player=request.user) | Q(game_master=request.user))
    characters = (
        Character.objects.prefetch_related("perks")
        .select_related(
            "player",
            "campaign__current_character",  # 'statistics' is not prefetched in order to always have fresh data
        )
        .filter(is_active=True)
    )
    if not request.user.is_superuser:
        characters = characters.filter(
            Q(player=request.user)
            | Q(campaign__game_master=request.user)
            | Q(is_player=True, campaign__view_pc=True)
            | Q(is_player=False, campaign__view_npc=True)
        )
    character = characters.filter(id=character_id).first()
    if not character:
        raise Http404()

    authorized = request.user and (
        request.user.is_superuser
        or (character and character.campaign and character.campaign.game_master_id == request.user.id)
    )
    characters = characters.filter(campaign_id=character.campaign_id if character else None)

    logs = Log.objects.select_related("player").filter(character=character)
    if not authorized:
        logs = logs.exclude(private=True)

    try:
        if request.method == "POST" and character:
            data = request.POST
            type, subtype, method = (
                data.get("type"),
                data.get("subtype"),
                data.get("method"),
            )
            if authorized and type == "stats":
                if "roll" in data:
                    result = character.roll(stats=data.get("roll"), modifier=int(data.get("modifier") or 0))
                    messages.add_message(
                        request,
                        result.message_level,
                        _("<strong>{pre_label}</strong> {label}").format(
                            pre_label=result.pre_label, label=result.long_label
                        ),
                    )
                elif "levelup" in data:
                    stats = data.get("levelup")
                    character.levelup(stats, 1, _ignore_log=True)
                elif method == "randomize":
                    if subtype == "special":
                        character.randomize_special(points=int(data.get("points") or 1), save=False)
                        if bool(data.get("stats", False)):
                            character.generate_stats(reset=True, save=False)
                        character.save()
                    elif subtype == "skill":
                        character.tag_skills = data.getlist("skills")
                        if not character.has_stats:
                            character.generate_stats(reset=True, save=False)
                        character.randomize_stats(
                            level=int(data.get("level") or 1),
                            balance=int(data.get("balance") or 0),
                            save=True,
                        )
            elif authorized and type == "fight" and data.get("target"):
                result = character.fight(
                    target=data.get("target"),
                    target_part=data.get("target_part"),
                    target_range=int(data.get("target_range")),
                    hit_chance_modifier=int(data.get("hit_chance_modifier") or 0),
                    force_success=bool(data.get("force_success", False)),
                    force_critical=bool(data.get("force_critical", False)),
                    force_raw_damage=bool(data.get("force_raw_damage", False)),
                    is_action=bool(data.get("is_action", False)),
                    weapon_type=data.get("weapon_type"),
                    fail_target=data.get("fail_target"),
                )
                messages.add_message(
                    request,
                    result.message_level,
                    _("<strong>{pre_label}</strong> {label}").format(
                        pre_label=result.pre_label, label=result.long_label
                    ),
                )
                if result.fail:
                    messages.add_message(
                        request,
                        result.message_level,
                        _("<strong>{pre_label}</strong> {label}").format(
                            pre_label=result.pre_label, label=result.long_label
                        ),
                    )
            elif authorized and type == "burst" and data.get("targets"):
                results = character.burst(
                    targets=list(zip(data.getlist("targets") or [], data.getlist("ranges") or [])),
                    hit_chance_modifier=int(data.get("hit_chance_modifier") or 0),
                    force_success=bool(data.get("force_success", False)),
                    force_critical=bool(data.get("force_critical", False)),
                    force_raw_damage=bool(data.get("force_raw_damage", False)),
                    is_action=bool(data.get("is_action", False)),
                    weapon_type=data.get("weapon_type"),
                )
                if data.get("weapon_type") == WEAPON_TYPE_GRENADE:
                    for result in results:
                        messages.add_message(
                            request,
                            result.message_level,
                            _("<strong>{pre_label}</strong> {label}").format(
                                pre_label=result.pre_label, label=result.long_label
                            ),
                        )
                else:
                    results = {}
                    for result in results:
                        results.setdefault(
                            result.defender,
                            dict(attacker=result.attacker, fail=0, success=0, damage=0),
                        )
                        results[result.defender]["fail"] += int(result.success is False)
                        results[result.defender]["success"] += int(result.success is True)
                        results[result.defender]["damage"] += result.damage.real_damage if result.damage else 0
                    for defender, result in results.items():
                        from django.contrib.messages import constants

                        messages.add_message(
                            request,
                            constants.SUCCESS if result["damage"] else constants.ERROR,
                            _(
                                "<strong>{attacker} vs {defender}</strong> {fail} coups ratés et {success} "
                                "coups au but pour {damage} dégâts"
                            ).format(defender=defender, **result),
                        )
            elif authorized and type == "damage":
                result = character.damage(
                    raw_damage=int(data.get("raw_damage") or 0),
                    min_damage=int(data.get("min_damage") or 0),
                    max_damage=int(data.get("max_damage") or 0),
                    damage_type=str(data.get("damage_type") or ""),
                    body_part=str(data.get("body_part") or ""),
                )
                messages.add_message(
                    request,
                    result.message_level,
                    _("<strong>{pre_label}</strong> {label}").format(pre_label=result.pre_label, label=result.label),
                )
            elif authorized and type == "item":
                item_id, item_name = data.get("item-id"), data.get("item-name")
                if method == "add":
                    quantity = int(data.get("quantity") or 1)
                    condition = int(data.get("condition") or 100) / 100.0
                    filter = dict(pk=item_id) if item_id else dict(name__icontains=item_name)
                    equip = Item.objects.filter(**filter).first()
                    equip.give(character=character, quantity=quantity, condition=condition)
                else:
                    is_action = bool(data.get("is_action", False))
                    equip = Equipment.objects.select_related("character", "item").filter(pk=item_id).first()
                    character = equip.character
                    if method == "equip":
                        equip.equip(is_action=is_action)
                    elif method == "reload":
                        equip.reload(is_action=is_action)
                    elif method == "use":
                        effects, modifiers = equip.use(is_action=is_action)
                        for effect in effects:
                            for damage in effect.damages:
                                messages.add_message(
                                    request,
                                    damage.message_level,
                                    _("<strong>{pre_label}</strong> {label}").format(
                                        pre_label=damage.pre_label, label=damage.label
                                    ),
                                )
                        for modifier in modifiers:
                            messages.add_message(
                                request,
                                modifier.message_level,
                                _("<strong>{pre_label}</strong> {label}").format(
                                    pre_label=character, label=modifier.label
                                ),
                            )
                    elif method == "repair":
                        equip.repair(value=int(data.get("condition") or 100), is_action=is_action)
                    elif method == "drop":
                        equip.drop(quantity=int(data.get("quantity") or 1), is_action=is_action)
                    elif method == "secondary":
                        equip.set_secondary()
            elif authorized and type == "effect":
                effect_id, effect_name = data.get("effect-id"), data.get("effect-name")
                if method == "add":
                    filter = dict(pk=effect_id) if effect_id else dict(name__icontains=effect_name)
                    effect = Effect.objects.filter(**filter).first().affect(character, force=True)
                    for damage in getattr(effect, "damages", []):
                        messages.add_message(
                            request,
                            damage.message_level,
                            _("<strong>{pre_label}</strong> {label}").format(
                                pre_label=damage.pre_label, label=damage.label
                            ),
                        )
                elif method == "remove":
                    scope = data.get("scope")
                    if scope == "character":
                        effect = CharacterEffect.objects.filter(pk=effect_id).first()
                        effect.delete() if effect else None
                    elif scope == "campaign":
                        effect = CampaignEffect.objects.filter(pk=effect_id).first()
                        effect.delete() if effect else None
            elif authorized and type == "action":
                character.health, character.action_points = int(data.get("hp")), int(data.get("ap"))
                character.experience, character.karma = int(data.get("xp")), int(data.get("karma"))
                character.money = int(data.get("money"))
                character.rads = int(data.get("rads"))
                character.thirst = int(data.get("thirst"))
                character.hunger = int(data.get("hunger"))
                character.sleep = int(data.get("sleep"))
                character.is_resting = bool(data.get("is_resting", False))
                character.save()
            elif type == "log":
                log_id, log_text, log_private = (
                    int(data.get("log") or 0),
                    data.get("text"),
                    bool(data.get("private")),
                )
                if log_id and method == "edit":
                    log_to_edit = logs.filter(id=log_id)
                    if not authorized:
                        log_to_edit = log_to_edit.filter(player=request.user)
                    log_to_edit.update(text=log_text)
                elif method == "add":
                    Log.objects.create(
                        player=request.user,
                        character=character,
                        text=log_text,
                        private=log_private,
                        game_date=getattr(character.campaign, "current_game_date", None),
                    )
        if request.method == "GET" and character:
            data = request.GET
            if "delete" in data:
                log_id = int(data.get("delete") or 0)
                log_to_delete = logs.filter(id=log_id)
                if not authorized:
                    log_to_delete = log_to_delete.filter(player=request.user)
                log_to_delete.delete()
    except ValidationError as error:
        for field, errors in error.message_dict.items():
            for error in errors if isinstance(errors, list) else [errors]:
                messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))
    except Exception as error:
        messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))

    inventory, effects = character.inventory, character.effects
    rollstats = RollHistory.get_stats(character)
    fightstats = FightHistory.get_stats(character)

    all_items = Item.objects.order_by("type", "name").only("id", "name", "type", "title").to_dict(display=True)
    all_effects = Effect.objects.filter(character__isnull=True).order_by("name").only("id", "name", "title").to_dict()

    return {
        "page": "character",
        "authorized": authorized,
        # Lists
        "campaigns": campaigns.distinct().order_by("name", "title"),
        "characters": characters.order_by("-is_player", "name", "title"),
        "logs": logs.order_by(*("game_date", "date") if "sort" in request.GET else ("-game_date", "-date")),
        # Character
        "character": character,
        "inventory": inventory,
        # Effects
        "character_effects": effects,
        "campaign_effects": character.campaign.effects if character.campaign else None,
        "perks": character.perks.prefetch_related("modifiers").all(),
        # Statistics
        "rollstats": rollstats,
        "fightstats": fightstats,
        # Enums
        "body_parts": BODY_PARTS,
        "damage_types": DAMAGES_TYPES,
        # Lists
        "all_items": all_items,
        "all_effects": all_effects,
    }


def next_turn(request, campaign_id):
    """
    Action pour passer au tour suivant
    """
    action = request.method == "POST"
    data = request.POST
    campaign = Campaign.objects.filter(id=campaign_id).first()
    if action and campaign and (request.user.is_superuser or campaign.game_master == request.user):
        # Prochain tour
        if "next" in data:
            next_character, damages = campaign.next_turn(seconds=int(data.get("seconds") or 0))
            for damage in damages:
                messages.add_message(
                    request,
                    damage.message_level,
                    _("<strong>{pre_label}</strong> {label}").format(pre_label=damage.pre_label, label=damage.label),
                )
            if next_character:
                return redirect("fallout:character", next_character.id)
        # Fin du tour
        if "cancel" in data:
            campaign.clear_turn()
            return redirect(data.get("page"))
    return redirect("fallout:campaign", campaign_id)


@login_required
@render_to("fallout/thumbnails.html")
def thumbnails(request):
    """
    Affiche les thumbnails d'un répertoire
    """
    import os

    from django.conf import settings

    directory = request.GET.get("dir") or ""
    if ".." in directory:
        raise Http404()
    directories = directory.split(os.sep)
    dirname = os.path.join(settings.STATIC_ROOT, "fallout/img/thumbnails", directory)
    if not os.path.exists(dirname) and settings.DEBUG:
        dirname = os.path.join(settings.BASE_DIR, "fallout/static/fallout/img/thumbnails", directory)
    images = []
    for filename in os.listdir(dirname):
        filepath = os.path.join(dirname, filename)
        title, ext = os.path.splitext(filename.replace("_", " "))
        filename = os.path.join(directory, filename)
        if os.path.isdir(filepath):
            images.append((title, True, filename))
        else:
            url = os.path.join("thumbnails", filename).replace("\\", "/")
            images.append((title, False, url))
    return {
        "page": "thumbnails",
        "directories": directories,
        "images": sorted(images, key=lambda e: e[0]),
    }


@login_required
@ajax_request
def simulation(request):
    """
    Réalise une simulation de combat
    """
    if request.method == "POST":
        try:
            data = request.POST
            attacker = Character.objects.select_related("statistics").get(pk=data.get("character"))
            if data.get("type") == "burst":
                targets = list(zip(data.getlist("targets") or [], data.getlist("ranges") or []))
                data = data.dict()
                data.pop("character"), data.pop("targets"), data.pop("ranges")
                results = attacker.burst(**data, targets=targets, simulation=True)
                return [result.to_dict(extra=("description",)) for result in results]
            elif data.get("target"):
                data = data.dict()
                data.pop("character")
                result = attacker.fight(**data, simulation=True)
                result_data = result.to_dict(extra=("description",))
                result_data["fail"] = result.fail.to_dict(extra=("description",)) if result.fail else None
                return result_data
        except Exception as error:  # noqa
            return _("Erreur : {error}").format(error=error)
    return ""


@login_required
@render_to("fallout/campaign/includes/rolls.html")
def view_campaign_rolls(request, campaign_id):
    limit = int(request.GET.get("limit") or "10")
    rolls = (
        RollHistory.objects.select_related("character")
        .filter(
            Q(character__player=request.user)
            | Q(character__campaign__game_master=request.user)
            | Q(character__is_player=True, character__campaign__view_pc=True)
            | Q(character__is_player=False, character__campaign__view_npc=True),
            character__campaign_id=campaign_id,
        )
        .order_by("-date")
        .only(
            "character__name",
            "value",
            "roll",
            "modifier",
            "stats",
            "success",
            "critical",
            "date",
        )[:limit]
    )
    damages = (
        DamageHistory.objects.select_related("character")
        .filter(
            Q(character__player=request.user)
            | Q(character__campaign__game_master=request.user)
            | Q(character__is_player=True, character__campaign__view_pc=True)
            | Q(character__is_player=False, character__campaign__view_npc=True),
            character__campaign_id=campaign_id,
            fight__isnull=True,
        )
        .order_by("-date")
        .only(
            "character__name",
            "damage_type",
            "base_damage",
            "real_damage",
            "body_part",
            "date",
        )[:limit]
    )
    fights = (
        FightHistory.objects.select_related("attacker", "defender", "damage")
        .filter(
            Q(attacker__player=request.user)
            | Q(attacker__campaign__game_master=request.user)
            | Q(attacker__is_player=True, attacker__campaign__view_pc=True)
            | Q(attacker__is_player=False, attacker__campaign__view_npc=True),
            attacker__campaign_id=campaign_id,
        )
        .order_by("-date")
        .only(
            "attacker__name",
            "defender__name",
            "status",
            "success",
            "critical",
            "body_part",
            "date",
            "damage__damage_type",
            "damage__base_damage",
            "damage__real_damage",
        )[:limit]
    )
    rolls = sorted(list(rolls) + list(damages) + list(fights), key=lambda r: r.date, reverse=True)[:limit]
    return {"rolls": rolls}


@login_required
@render_to("fallout/items.html")
def items(request):
    return {"items": Item.objects.prefetch_related("modifiers").order_by("type", "name")}


@login_required
@render_to("fallout/character.html")
def create_character(request, campaign_id=None):
    campaign = Campaign.objects.filter(id=campaign_id).first()
    if campaign_id and not campaign:
        raise Http404()
    if not (request.user and (request.user.is_superuser or (campaign and campaign.game_master_id == request.user.id))):
        raise Http404()

    form = QuickCreateCharacterForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = to_object(form.cleaned_data)
        character = Character.objects.create(
            name=data.name,
            race=data.race,
            tag_skills=data.tag_skills,
            campaign_id=campaign_id,
            has_stats=False,
            has_needs=False,
        )
        if data.points:
            character.randomize_special(**form.cleaned_data, save=False)
        character.generate_stats(**form.cleaned_data, save=False)
        character.randomize_stats(**form.cleaned_data, save=False)
        character.equip(**form.cleaned_data)
        character.save()
        return redirect("fallout:character", character.id)
    return {"form": form}
