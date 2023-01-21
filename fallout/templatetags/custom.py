# coding: utf-8
from django import template

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
