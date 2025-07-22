from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Allows accessing dictionary items by key in Django templates.
    Usage: {{ my_dict|get_item:my_key }}
    Returns None if the key doesn't exist.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter(name='get_range')
def get_range(value):
    """
    Returns a range of numbers.
    Usage: {% for i in 5|get_range %} -> loops 0, 1, 2, 3, 4
    """
    return range(value)


