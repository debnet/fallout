# coding: utf-8
from common.api.utils import create_api, disable_relation_fields

from rpg.fallout.models import MODELS


# Désactive les listes déroulantes sur les champs de relations
disable_relation_fields(*MODELS)

# Création des APIs REST standard pour les modèles de cette application
router, *_ = create_api(*MODELS)
