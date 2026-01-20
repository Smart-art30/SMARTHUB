from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    """Get value from dictionary safely."""
    if d is None:
        return ''
    return d.get(key, '')
