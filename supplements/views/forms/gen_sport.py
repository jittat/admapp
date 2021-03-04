from django import forms

SPORT_CHOICES = [
    'กรีฑา',
    'กอล์ฟ',
    'ครอสเวิร์ด',
    'คาราเต้โด',
    'เซปัคตะกร้อ',
    'ซอฟท์บอล',
    'ดาบไทย',
    'ดาบสากล',
    'เทควันโด',
    'เทนนิส',
    'เทเบิลเทนนิส',
    'บาสเกตบอล',
    'แบดมินตัน',
    'โบว์ลิ่ง',
    'บริดจ์',
    'เปตอง',
    'ฟุตซอล',
    'ฟุตบอล',
    'มวยสมัครเล่น',
    'ยิงธนู',
    'ยิงปืน',
    'ยูโด',
    'รักบี้ฟุตบอล',
    'เรือพาย',
    'ลีลาศ',
    'วอลเลย์บอล',
    'ว่ายน้ำ/โปโลน้ำ',
    'หมากกระดาน',
    'แฮนด์บอล',
    'ฮอกกี้',
    'กีฬาอื่นๆ',
]

GEN_SPORT_LEVEL_CHOICES = [
    ('101': 'นักกีฬาตัวแทนทีมชาติไทย'),
    ('102': 'นักกีฬาตัวแทนเยาวชนทีมชาติไทย'),
    ('103': 'กีฬาแห่งชาติ ได้อันดับที่ 1 – 3 (รอบการแข่งขันระดับประเทศ)'),
    ('204': 'กีฬาชิงชนะเลิศแห่งประเทศไทย ประเภททั่วไป ได้อันดับที่ 1 – 3'),
    ('205': 'กีฬามหาวิทยาลัยแห่งประเทศไทย หรือกีฬาอุดมศึกษา ได้อันดับที่ 1 – 3'),
    ('206': 'กีฬาเยาวชนแห่งชาติ ได้อันดับที่ 1 – 3 (รอบการแข่งขันระดับประเทศ)'),
    ('207': 'ตัวแทนนักเรียนเข้าแข่งขันกีฬาในระดับนานาชาติ ที่ดำเนินการโดยกรมพลศึกษา'),
    ('208': 'กีฬาเยาวชนชิงชนะเลิศแห่งประเทศไทย ได้อันดับที่ 1 – 3'),
    ('209': 'กีฬาที่มหาวิทยาลัยเกษตรศาสตร์จัดการแข่งขัน ได้อันดับที่ 1 – 3'),
    ('210': 'กีฬานักเรียนนักศึกษาแห่งชาติ ได้อันดับที่ 1 – 3 (รอบการแข่งขันระดับประเทศ)'),
    ('211': 'กีฬานักเรียนการศึกษาขั้นพื้นฐาน ได้อันดับที่ 1 – 3 (รอบการแข่งขันระดับประเทศ)'),
    ('212': 'กีฬากรมพลศึกษา ได้อันดับที่ 1 – 3'),
    ('213': 'กีฬาระหว่างโรงเรียนกีฬา ได้อันดับที่ 1 – 3 (รอบการแข่งขันระดับประเทศ)'),
    ('214': 'กีฬากรุงเทพมหานคร ได้อันดับที่ 1 – 3'),
    ('215': 'กีฬาสาธิตสามัคคี ได้อันดับที่ 1'),
    ('216': 'กีฬาดาวรุ่ง (จัดการแข่งขันโดยสมาคมกีฬาแห่งประเทศไทย) ได้อันดับที่ 1'),
    ('217': 'กีฬาที่เข้าแข่งขันในรายการแข่งขันที่มหาวิทยาลัยเกษตรศาสตร์กำหนด'),
]

class GenSportTypeForm(forms.Form):
    gen_sport_type = forms.ChoiceField(label='กรุณาระบุประเภทกีฬา',
                                   choices=zip(SPORT_CHOICES,SPORT_CHOICES))
    gen_sport_level = forms.ChoiceField(label='กรุณาระบุระดับการเป็นตัวแทน',
                                        choices=GEN_SPORT_LEVEL_CHOICES)

def init_sport_type_form(request,
                         applicant,
                         admission_project,
                         admission_round,
                         form_prefix,
                         current_data):

    if (current_data) and ('gen_sport_type' in current_data):
        initial = { 'gen_sport_type': current_data['gen_sport_type'] }
        if 'gen_sport_level' in current_data:
            initial['gen_sport_level'] = current_data['gen_sport_level']
        form = GenSportTypeForm(prefix=form_prefix,
                             initial=initial)
    else:
        current_type = '-'
        form = GenSportTypeForm(prefix=form_prefix)
        
    return {
        'form': form,
    }


def process_sport_type_form(request,
                            applicant,
                            admission_project,
                            admission_round,
                            form_prefix,
                            current_data):

    form = GenSportTypeForm(request.POST, prefix=form_prefix)
    if form.is_valid():
        return (True, {
            'gen_sport_type': form.cleaned_data['gen_sport_type'],
            'gen_sport_level': form.cleaned_data['gen_sport_level'],
        })
    else:
        return (False, {})


def init_sport_history_form(request,
                            applicant,
                            admission_project,
                            admission_round,
                            form_prefix,
                            current_data):

    if current_data == {}:
        current_data = []
    return { 'history_count': len(current_data),
             'history_data': current_data,
             'form_prefix': form_prefix }


def process_sport_history_form(request,
                               applicant,
                               admission_project,
                               admission_round,
                               form_prefix,
                               current_data):
    title_name = form_prefix + 'title[]'
    if title_name not in request.POST:
        return (False, {})

    row_count = len(request.POST.getlist(title_name))
    data = []
    for r in range(row_count):
        res = {'title': request.POST.getlist(title_name)[r],
               'dates': request.POST.getlist(form_prefix + 'dates[]')[r],
               'location': request.POST.getlist(form_prefix + 'location[]')[r],
               'result': request.POST.getlist(form_prefix + 'result[]')[r],}
        data.append(res)

    return (True, data)
