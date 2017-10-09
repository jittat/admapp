from django import template

register = template.Library()

def thaidate(date):
    MONTHS = ['','มกราคม','กุมภาพันธ์','มีนาคม','เมษายน',
              'พฤษภาคม','มิถุนายน','กรกฎาคม','สิงหาคม',
              'กันยายน','ตุลาคม','พฤศจิกายน','ธันวาคม']
    day = date.day
    month = MONTHS[date.month]
    year = date.year
    return '%d %s %d' % (day,month,year + 543)

def uploadeddocument_name(doc):
    if len(doc.detail) > 0:
        return doc.detail
    return doc.uploaded_file.name.split('/')[-1]
register.filter('thaidate',thaidate)
register.filter('uploadeddocument_name',uploadeddocument_name)
