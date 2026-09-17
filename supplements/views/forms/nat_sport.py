from django import forms

SPORT_CHOICES = [
    "ว่ายน้ำ",
    "โปโลน้ำ",
    "วอลเลย์บอล",
    "วอลเลย์บอลชายหาด",
    "เทควันโด",
    "มวย",
    "กรีฑา",
    "ฟุตบอล",
    "บาสเกตบอล",
    "เปตอง",
    "เซปักตะกร้อ",
    "เทเบิลเทนนิส",
    "แบดมินตัน",
    "ฟุตซอล",
    "อีสปอร์ต",
    "วู้ดบอล",
    "ยูยิตสู",
    "ปันจักสีลัต",
    "เทนนิส",
    "ฮับกิโด",
    "จานร่อน",
    "หมากรุกไทย",
    "หมากรุกสากล",
    "หมากฮอส",
    "หมากรุกอาเซียน",
    "หมากล้อม",
    "บริดจ์",
    "ดาบไทย",
    "ซอฟท์บอล",
    "เบสบอล",
    "เรือพาย",
    "คาราเต้",
    "ดาบสากล",
    "แฮนด์บอล",
    "ฮอกกี้",
    "รักบี้ฟุตบอล",
    "คอร์ฟบอล",
    "วูซู",
    "ยูโด",
    "ครอสเวิร์ด",
    "เอแม็ท",
    "กอล์ฟ",
    "โบว์ลิ่ง",
    "เพาะกาย",
    "ยิงธนู",
    "ยิงปืน",
    "ลีลาศ",
]

class SportTypeForm(forms.Form):
    sport_type = forms.ChoiceField(label='กรุณาระบุประเภทกีฬา',
                                   choices=zip(SPORT_CHOICES,SPORT_CHOICES))
    sport_level = forms.ChoiceField(label='กรุณาระบุระดับผลงาน',
                                    choices=[('ตัวแทนทีมชาติไทย','ตัวแทนทีมชาติไทย'),
                                             ('เยาวชนทีมชาติไทย','เยาวชนทีมชาติไทย')])

def init_sport_type_form(request,
                         applicant,
                         admission_project,
                         admission_round,
                         form_prefix,
                         current_data):

    if (current_data) and ('sport_type' in current_data):
        initial = { 'sport_type': current_data['sport_type'] }
        if 'sport_level' in current_data:
            initial['sport_level'] = current_data['sport_level']
        form = SportTypeForm(prefix=form_prefix,
                             initial=initial)
    else:
        current_type = '-'
        form = SportTypeForm(prefix=form_prefix)
        
    return {
        'form': form,
    }


def process_sport_type_form(request,
                            applicant,
                            admission_project,
                            admission_round,
                            form_prefix,
                            current_data):

    form = SportTypeForm(request.POST, prefix=form_prefix)
    if form.is_valid():
        return (True, {
            'sport_type': form.cleaned_data['sport_type'],
            'sport_level': form.cleaned_data['sport_level'],
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
