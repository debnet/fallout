# coding: utf-8
from rest_framework.serializers import ModelSerializer, MultipleChoiceField

# Patch de django-multiselectfield pour compatibilité Django 2
# https://github.com/goinnn/django-multiselectfield/issues/74
try:

    def value_to_string(self, obj):
        try:
            value = self.val_from_object(obj)
        except AttributeError:
            value = self.value_from_object(obj)
        return self.get_prep_value(value)

    from multiselectfield.db.fields import MultiSelectField

    MultiSelectField.value_to_string = value_to_string

    # Patch des serializers DRF pour la gestion des champs MultiSelectField
    def build_standard_field(self, field_name, model_field):
        field_class, field_kwargs = self._build_standard_field(field_name, model_field)
        if isinstance(model_field, MultiSelectField):
            return MultipleChoiceField, field_kwargs
        return field_class, field_kwargs

    ModelSerializer._build_standard_field = ModelSerializer.build_standard_field
    ModelSerializer.build_standard_field = build_standard_field
except ImportError:
    pass
