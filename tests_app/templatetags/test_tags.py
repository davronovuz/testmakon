from django import template

register = template.Library()

@register.filter
def to_char(value):
    try:
        return chr(int(value))
    except (ValueError, TypeError):
        return ""