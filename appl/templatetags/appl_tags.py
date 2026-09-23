from django import template

from django.conf import settings
from django.urls import translate_url

register = template.Library()

@register.simple_tag
def admission_year():
    return settings.ADMISSION_YEAR

@register.simple_tag
def short_admission_year():
    return str(settings.ADMISSION_YEAR % 100)

@register.simple_tag
def web_branding():
    return settings.WEB_BRANDING

@register.simple_tag
def web_title():
    return settings.WEB_TITLE

@register.simple_tag(takes_context=True)
def translated_url(context, lang_code):
    """The current page's URL (with query string) in another language."""
    return translate_url(context['request'].get_full_path(), lang_code)

@register.filter
def thaidate(date):
    MONTHS = ['','มกราคม','กุมภาพันธ์','มีนาคม','เมษายน',
              'พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม',
              'กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม']
    day = date.day
    month = MONTHS[date.month]
    year = date.year
    return '%d %s %d' % (day,month,year + 543)

@register.filter
def uploadeddocument_name(doc):
    if len(doc.detail) > 0:
        return doc.detail
    return doc.uploaded_file.name.split('/')[-1]

import re

image_regex = re.compile(r'(img::[^ \t\n\r]+)', re.MULTILINE)

@register.filter(is_safe=True)
def imagify(value):
    def _replace(match):
        img_str = match.group(0)[5:]
        return f'<img src="https://{img_str}">'

    return image_regex.sub(_replace, value)
