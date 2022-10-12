import json

from django import template
from django.utils.safestring import mark_safe

from criteria.criteria_options import CRITERIA_OPTIONS

register = template.Library()

@register.simple_tag
def criteria_options_as_js():
    items = []
    for cname in CRITERIA_OPTIONS:
        items.append(f'const {cname} = ' +
                     json.dumps(CRITERIA_OPTIONS[cname]))

    return mark_safe('\n'.join(items))
