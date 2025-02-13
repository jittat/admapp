from django import forms

"""
ABILITY_CHOICES = [
    'ดนตรีไทย (ระนาดเอก)',
    'ดนตรีไทย (ระนาดทุ้ม)',
    'ดนตรีไทย (ฆ้องวงใหญ่)',
    'ดนตรีไทย (ฆ้องวงเล็ก)',
    'ดนตรีไทย (ตะโพนไทย)',
    'ดนตรีไทย (ปี่ใน)',
    'ดนตรีไทย (ขลุ่ย)',
    'ดนตรีไทย (ซอด้วง)',
    'ดนตรีไทย (ซออู้)',
    'ดนตรีไทย (กลองทัด)',
    'ดนตรีไทย (กลองแขก)',
    'ดนตรีสากล (เครื่องเป่า)',
    'ดนตรีสากล (กีตาร์)',
    'ดนตรีสากล (เบส)',
    'ดนตรีสากล (คีย์บอร์ด)',
    'ดนตรีสากล (เปียโน)',
    'ดนตรีสากล (กลองชุด)',
    'ดนตรีสากล (เพอร์คัชชั่น)',
    'ดนตรีสากล (ไวโอลิน)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (พิณ)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (โปงลาง)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (กลองหาง)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (แคน)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (โหวต)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (นางไห)',
    'รำไทย - นาฏศิลป์ไทย (ละครพระ)',
    'รำไทย - นาฏศิลป์ไทย (ละครนาง)',
    'รำไทย - โขน (พระ)',
    'รำไทย - โขน (นาง)',
    'รำไทย - โขน (ยักษ์)',
    'รำไทย - โขน (ลิง)',
    'รำไทย - โขน (ละครพระ)',
    'รำไทย - โขน (ละครนาง)',
    'ขับร้อง (เพลงไทยเดิม)',
    'ขับร้อง (เพลงไทยลูกทุ่ง)',
    'ขับร้อง (เพลงประสานเสียง)',
]
"""

EXAM_CHOICES = [
    'นาฏศิลป์ไทย - ละครพระ',
    'นาฏศิลป์ไทย - ละครนาง',
    'นิสิตอีสาน - กีตาร์ เปียโนหรือคีย์บอร์ด เบส กลองชุด',
    'นิสิตอีสาน - เครื่องดนตรีพื้นบ้านพื้นเมืองอีสาน',
    'นิสิตอีสาน - ขับร้องเพลงไทยลูกทุ่ง',
    'นิสิตอีสาน - นาฏศิลป์พื้นเมืองภาคอีสาน',
    'ขับร้องประสานเสียงแห่งมหาวิทยาลัยเกษตรศาสตร์ - เปียโนหรือคีย์บอร์ด',
    'ขับร้องประสานเสียงแห่งมหาวิทยาลัยเกษตรศาสตร์ - ขับร้องเพลงประสานเสียง',
    'วงดนตรีสากล มหาวิทยาลัยเกษตรศาสตร์ - เปียโนหรือคีย์บอร์ด',
    'วงดนตรีสากล มหาวิทยาลัยเกษตรศาสตร์ - เบส',
    'วงดนตรีสากล มหาวิทยาลัยเกษตรศาสตร์ - เพอร์คัชชั่น',
    'วงดนตรีสากล มหาวิทยาลัยเกษตรศาสตร์ - Saxophone Trumpet Trombone',
    'ดนตรีไทย - ระนาดเอก ระนาดทุ้ม ฆ้องวงใหญ่ ฆ้องวงเล็ก ปี่ใน',
    'ดนตรีไทย - ตะโพนไทย กลองแขก กลองทัด',
    'ดนตรีไทย - ซอด้วง ซออู้ จะเข้ ขิม ขลุ่ย',
    'ดนตรีไทย - ขับร้อง',
    'วงดนตรีรวมดาวกระจุย - Saxophone Trumpet Trombone Alto saxophone Tenner saxophone',
    'วงดนตรีรวมดาวกระจุย - กลองชุด กีตาร์ เบส คีย์บอร์ด',
    'วงดนตรีรวมดาวกระจุย - ขับร้องเพลงไทยลูกทุ่ง',
    'โขนละคอน - โขนพระ โขนนาง ยักษ์ ลิง',
    'โขนละคอน - ประเภทละคร (พระ, นาง)',
    'อคูสติก - เปียโนหรือคีย์บอร์ด',
    'อคูสติก - เพอร์คัชชั่น',
    'อคูสติก - Saxophone Trumpet',
    'อคูสติก - กีตาร์โปร่ง',
    'ส่งเสริมและเผยแพร่ศิลปวัฒนธรรมภาคเหนือ - นาฏศิลป์พื้นเมืองภาคเหนือ (หญิง)',
    'ส่งเสริมและเผยแพร่ศิลปวัฒนธรรมภาคเหนือ - นาฏศิลป์พื้นเมืองภาคเหนือ (ชาย)',
    'ส่งเสริมและเผยแพร่ศิลปวัฒนธรรมภาคเหนือ - เครื่องดนตรีเหนือ',
    'กิจกรรมส่วนกลาง - ออกแบบแฟชั่น / ออกแบบผลิตภัณฑ์ชุมชน',
    'กิจกรรมส่วนกลาง - ดารา นักแสดง ศิลปิน หรือนักร้อง Influencer',
    'กิจกรรมส่วนกลาง - นักสร้างเนื้อหา (content creator)',
]

"""
class CulturalTypeForm(forms.Form):
    cultural_type = forms.ChoiceField(label='กรุณาระบุประเภทศิลปวัฒนธรรม',
                                      choices=zip(ABILITY_CHOICES, ABILITY_CHOICES))
"""

class CulturalExamForm(forms.Form):
    cultural_exam = forms.ChoiceField(label='กรุณาระบุชมรมและสาขาที่ต้องการทดสอบ',
                                      choices=zip(EXAM_CHOICES, EXAM_CHOICES))

"""
def init_cultural_type_form(request,
                            applicant,
                            admission_project,
                            admission_round,
                            form_prefix,
                            current_data):

    if (current_data) and ('cultural_type' in current_data):
        initial = { 'cultural_type': current_data['cultural_type'] }
        form = CulturalTypeForm(prefix=form_prefix,
                                initial=initial)
    else:
        current_type = '-'
        form = CulturalTypeForm(prefix=form_prefix)
        
    return {
        'form': form,
    }


def process_cultural_type_form(request,
                               applicant,
                               admission_project,
                               admission_round,
                               form_prefix,
                               current_data):

    form = CulturalTypeForm(request.POST, prefix=form_prefix)
    if form.is_valid():
        return (True, {
            'cultural_type': form.cleaned_data['cultural_type'],
        })
    else:
        return (False, {})

"""

def init_cultural_history_form(request,
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


def process_cultural_history_form(request,
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


def init_cultural_exam_form(request,
                            applicant,
                            admission_project,
                            admission_round,
                            form_prefix,
                            current_data):

    if (current_data) and ('cultural_exam' in current_data):
        initial = { 'cultural_exam': current_data['cultural_exam'] }
        form = CulturalExamForm(prefix=form_prefix,
                                initial=initial)
    else:
        current_type = '-'
        form = CulturalExamForm(prefix=form_prefix)
        
    return {
        'form': form,
    }


def process_cultural_exam_form(request,
                               applicant,
                               admission_project,
                               admission_round,
                               form_prefix,
                               current_data):

    form = CulturalExamForm(request.POST, prefix=form_prefix)
    if form.is_valid():
        return (True, {
            'cultural_exam': form.cleaned_data['cultural_exam'],
        })
    else:
        return (False, {})



