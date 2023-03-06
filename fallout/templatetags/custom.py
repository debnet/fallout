# coding: utf-8
from copy import copy
import types
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter("range")
def irange(stop, start=0):
    reverse = stop < start
    return range(int(start), int(stop) - 1 if reverse else int(stop) + 1, -1 if reverse else 1)


@register.filter("min")
def imin(value, mini=0):
    return min(mini, value)


@register.filter("max")
def imax(value, maxi=0):
    return max(maxi, value)


def silence_without_field(fn):
    def wrapped(field, attr):
        if not field:
            return ""
        return fn(field, attr)

    return wrapped


def _process_field_attributes(field, attr, process):
    # split attribute name and value from 'attr:value' string
    params = attr.split(":", 1)
    attribute = params[0]
    value = params[1] if len(params) == 2 else ""
    field = copy(field)
    # decorate field.as_widget method with updated attributes
    if hasattr(field, "as_widget"):
        old_as_widget = field.as_widget

        def as_widget(self, widget=None, attrs=None, only_initial=False):
            attrs = attrs or {}
            process(widget or self.field.widget, attrs, attribute, value)
            html = old_as_widget(widget, attrs, only_initial)
            self.as_widget = old_as_widget
            return html

        field.as_widget = types.MethodType(as_widget, field)
    elif isinstance(field, str):
        key, value = params
        return mark_safe(field.replace(">", f' {key}="{value}">'))
    return field


@register.filter("attr")
@silence_without_field
def set_attr(field, attr):
    def process(widget, attrs, attribute, value):
        attrs[attribute] = value

    return _process_field_attributes(field, attr, process)


@register.filter("add_error_attr")
@silence_without_field
def add_error_attr(field, attr):
    if hasattr(field, "errors") and field.errors:
        return set_attr(field, attr)
    return field


@register.filter("append_attr")
@silence_without_field
def append_attr(field, attr):
    def process(widget, attrs, attribute, value):
        if attrs.get(attribute):
            attrs[attribute] += " " + value
        elif widget.attrs.get(attribute):
            attrs[attribute] = widget.attrs[attribute] + " " + value
        else:
            attrs[attribute] = value

    return _process_field_attributes(field, attr, process)


@register.filter("add_class")
@silence_without_field
def add_class(field, css_class):
    return append_attr(field, "class:" + css_class)


@register.filter("add_error_class")
@silence_without_field
def add_error_class(field, css_class):
    if hasattr(field, "errors") and field.errors:
        return add_class(field, css_class)
    return field


@register.filter("set_data")
@silence_without_field
def set_data(field, data):
    return set_attr(field, "data-" + data)
