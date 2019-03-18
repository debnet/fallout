# coding: utf-8
import ast

from django import template
from django.template import Node


register = template.Library()


@register.filter('range')
def irange(stop, start=0):
    reverse = stop < start
    return range(int(start), int(stop) - 1 if reverse else int(stop) + 1, -1 if reverse else 1)


@register.filter('min')
def imin(value, mini=0):
    return min(mini, value)


@register.filter('max')
def imax(value, maxi=0):
    return max(maxi, value)


class MarkdownNode(Node):
    """
    Classe utilitaire pour le template tag markdown
    """
    def __init__(self, nodelist, *extras):
        self.nodelist = nodelist
        self.extras = extras

    def render(self, context):
        output = self.nodelist.render(context)
        import markdown2
        return markdown2.markdown(output.strip(), extras=self.extras)


@register.tag(name='markdown')
def tag_markdown(parser, token):
    """
    Permet de convertir un format markdown en HTML
    """
    nodelist = parser.parse(('endmarkdown',))
    parser.delete_first_token()
    args = [ast.literal_eval(bit) for bit in token.split_contents()[1:]]
    return MarkdownNode(nodelist, *args)
