from django import template

register = template.Library()

@register.filter
def force_https(value):
    """Replace http:// with https:// at the start of a URL"""
    if isinstance(value, str) and value.startswith("http://"):
        return value.replace("http://", "https://", 1)
    return value