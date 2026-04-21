from html import unescape

from django import template


register = template.Library()


@register.filter
def html_unescape(value):
    if value is None:
        return ''
    return unescape(str(value))
