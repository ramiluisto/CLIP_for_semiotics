"""
Custom template filters for analysis app.
"""

from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter to get item from dictionary by key.

    Usage: {{ my_dict|get_item:my_key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter(name='mul')
def mul(value, arg):
    """
    Multiply filter for calculations in templates.

    Usage: {{ value|mul:10 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='div')
def div(value, arg):
    """
    Division filter for calculations in templates.

    Usage: {{ value|div:10 }}
    """
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='add')
def add(value, arg):
    """
    Addition filter for calculations in templates.

    Usage: {{ value|add:10 }}
    """
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0
