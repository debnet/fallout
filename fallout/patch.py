# coding: utf-8

# Patch de django-multiselectfield pour compatibilité Django 2
# https://github.com/goinnn/django-multiselectfield/issues/74
try:
    def value_to_string(self, obj):
        try:
            value = self.val_from_object(obj)
        except AttributeError:
            value = self.value_from_object(obj)
        return self.get_prep_value(value)

    from multiselectfield.db import fields
    fields.MultiSelectField.value_to_string = value_to_string
except ImportError:
    pass
