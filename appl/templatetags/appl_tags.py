from django import template

from django.conf import settings

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

