# coding: utf-8
from django import forms
from django.db import models
from django.utils.text import capfirst


class MultipleChoiceFormField(forms.MultipleChoiceField):
    widget = forms.CheckboxSelectMultiple


class MultipleChoiceField(models.TextField):

    def formfield(self, **kwargs):
        defaults = {
            'required': not self.blank,
            'label': capfirst(self.verbose_name),
            'help_text': self.help_text,
            'choices': self.choices}
        if self.has_default():
            defaults['initial'] = self.get_default()
        defaults.update(kwargs)
        return MultipleChoiceFormField(**defaults)

    def validate(self, value, model_instance):
        choices = set(a for a, b in self.flatchoices)
        if set(value) & choices == set(value):
            return
        return super().validate(value, model_instance)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)

    def get_prep_value(self, value):
        return '' if value is None else ','.join(value)

    def get_db_prep_save(self, value, connection, prepared=False):
        if not prepared and not isinstance(value, str):
            value = self.get_prep_value(value)
        return value

    def to_python(self, value):
        import re
        choices = dict(self.flatchoices)
        if not choices:
            return []
        return list(re.split(r'[^\w]', value) if isinstance(value, str) else value)

    def from_db_value(self, value, *args, **kwargs):
        if value is None:
            return value
        return self.to_python(value)
