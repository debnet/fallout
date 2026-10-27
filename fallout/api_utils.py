# coding: utf-8
import logging
from functools import wraps

from common.api.utils import api_view_with_serializer as common_api_view
from django.core.exceptions import PermissionDenied as ModelPermissionDenied
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404
from django.utils.translation import gettext as _
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def api_view_with_serializer(http_method_names=None, input_serializer=None, serializer=None):
    """Conserve simulation et erreurs métier ; common valide les entrées et assure la transaction."""

    def decorate(function):
        @wraps(function)
        def handle(request, *args, **kwargs):
            try:
                context = {"request": request, "view": request.parser_context["view"]}
                simulation = bool(getattr(request, "validated_data", {}).get("simulation"))
                result = function(request, *args, **kwargs)
                if not isinstance(result, Response):
                    if serializer:
                        result = serializer(result, many=isinstance(result, (list, QuerySet)), context=context).data
                    result = Response(result)
                if simulation:
                    # Annuler aussi les écritures indirectes et la sérialisation d'une simulation.
                    transaction.set_rollback(True)
                return result
            except (APIException, Http404, ModelPermissionDenied, ModelValidationError):
                raise
            except AssertionError as error:
                raise ValidationError(str(error) or _("Action impossible.")) from error
            except Exception as error:
                logger.exception("Échec d'une opération API")
                raise APIException(_("Une erreur interne a empêché cette opération.")) from error

        return common_api_view(
            http_method_names,
            input_serializer=input_serializer,
            atomic=True,
        )(handle)

    return decorate
