from django import template

register = template.Library()

@register.simple_tag
def dnone_flag(flags, key):
    if flags.get(key,False) == False:
        return 'd-none'
    else:
        return ''
