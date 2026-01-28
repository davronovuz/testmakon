from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Lug'atdan kalit bo'yicha qiymatni olish uchun filtr"""
    if dictionary:
        return dictionary.get(key)
    return None