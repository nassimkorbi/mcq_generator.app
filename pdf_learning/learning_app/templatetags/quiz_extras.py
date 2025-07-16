from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to lookup dictionary values"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''

@register.filter
def add(value, arg):
    """Add the arg to the value."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        try:
            return value + arg
        except Exception:
            return ''

@register.simple_tag
def get_correct_count(questions):
    """Get count of correct answers"""
    return sum(1 for q in questions if q.is_correct)

@register.simple_tag
def get_incorrect_count(questions):
    """Get count of incorrect answers"""
    return sum(1 for q in questions if not q.is_correct)
