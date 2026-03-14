from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Dict dan variable key bilan qiymat olish: dict|get_item:key"""
    if dictionary is None:
        return None
    return dictionary.get(key)
