SPORT_CHOICES = [
    'ฟุตบอล',
    'วอลเลย์บอล/วอลเลย์บอลชายหาด',
    'บาสเกตบอล',
    'รักบี้ฟุตบอล',
    'ตะกร้อ',
    'ยูโด',
    'ยิงปืน',
    'แบดมินตัน',
    'เทควันโด',
    'ทางน้ำ (ว่ายน้ำและโปโลน้ำ)',
    'เรือพาย',
    'เทนนิส',
    'ดาบสากล',
    'กรีฑา',
    'คาราเต้-โด',
    'เทเบิลเทนนิส',
    'กอล์ฟ',
    'โบว์ลิ่ง',
    'ลีลาศ',
    'เปตอง',
    'มวย (มวยไทยและมวยสากล)',
    'ซอฟท์บอลและเบสบอล',
    'หมากล้อม',
    'หมากกระดาน',
    'ครอสเวิร์ด',
    'ยิงธนู',
    'ฮอกกี้',
    'แฮนด์บอล',
    'บริดจ์',
    'ฟุตซอล',
]

def init_form(request,
              applicant,
              admission_project,
              admission_round,
              form_prefix,
              current_data):

    if (current_data) and ('sport_type' in current_data):
        current_type = current_data['sport_type']
    else:
        current_type = '-'

    return {
        'sport_choices': SPORT_CHOICES,
        'current_type': current_type,
    }


def process_sport_type(request,
                       applicant,
                       admission_project,
                       admission_round,
                       form_prefix,
                       current_data):
    
    field_name = form_prefix + 'type'
    if field_name in request.POST:
        return (True, {
            'sport_type': request.POST[field_name],
        })
    else:
        return (False, {})
