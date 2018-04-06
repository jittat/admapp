from django import template
from django.utils.safestring import mark_safe

register = template.Library()

def format_single_score(value):
    if value == -1:
        return '-'
    elif value == '':
        return ''
    else:
        return '%.2f' % (value,)

@register.filter(name='score')
def score(value):
    return format_single_score(value)

@register.filter(name='score_array')
def score_array(value):
    if value == '':
        return ''
    else:
        return mark_safe('<br/>'.join([format_single_score(s) for s in value]))
    
@register.filter(name='round_array')
def round_array(value):
    if value == '':
        return ''
    else:
        return mark_safe('<br/>'.join([str(s) for s in value]))
