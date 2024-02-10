from django import template

register = template.Library()

@register.simple_tag
def dnone_flag(flags, key):
    none_val = False
    if key.startswith('-'):
        key = key[1:]
        none_val = True
    if flags.get(key,False) == none_val:
        return 'd-none'
    else:
        return ''
