from django import forms

ABILITY_CHOICES = [
    'ดนตรีไทย (ระนาดเอก)',
    'ดนตรีไทย (ระนาดทุ้ม)',
    'ดนตรีไทย (ฆ้องวงใหญ่)',
    'ดนตรีไทย (ฆ้องวงเล็ก)',
    'ดนตรีไทย (ปี่ใน)',
    'ดนตรีไทย (ตะโพนไทย)',
    'ดนตรีไทย (ซอด้วง)',
    'ดนตรีไทย (ซออู้)',
    'ดนตรีไทย (ขลุ่ย)',
    'ดนตรีไทย (กลองแขก)',
    'ดนตรีไทย (จะเข้)',
    'ดนตรีสากล (เครื่องเป่า)',
    'ดนตรีสากล (กีตาร์)',
    'ดนตรีสากล (คีย์บอร์ด)',
    'ดนตรีสากล (เปียโน)',
    'ดนตรีสากล (เบส)',
    'ดนตรีสากล (เพอร์คัชชั่น)',
    'ดนตรีสากล (กลองชุด)',
    'ดนตรีสากล (ไวโอลิน)',
    'ดนตรีสากล (วิโอล่า)',
    'ดนตรีสากล (เชลโล่)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (พิณ)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (โปงลาง)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (แคน)',
    'ดนตรีพื้นบ้านพื้นเมืองอีสาน (โหวต)',
    'นาฏศิลป์ไทย (ละครพระ)',
    'นาฏศิลป์ไทย (ละครนาง)',
    'นาฏศิลป์ไทย - โขน (พระ)',
    'นาฏศิลป์ไทย - โขน (นาง)',
    'นาฏศิลป์ไทย - โขน (ยักษ์)',
    'นาฏศิลป์ไทย - โขน (ลิง)',
    'ขับร้อง (เพลงไทยเดิม)',
    'ขับร้อง (เพลงไทยลูกทุ่ง)',
    'ขับร้อง (เพลงไทยสากล)',
    'ขับร้อง (ขับร้องประสานเสียง)',
]

EXAM_CHOICES = [
    'ชมรมดนตรีไทย - ขับร้องเพลงไทยเดิม',
    'ชมรมดนตรีไทย - ระนาดเอก',
    'ชมรมดนตรีไทย - ระนาดทุ้ม',
    'ชมรมดนตรีไทย - ฆ้องวงใหญ่',
    'ชมรมดนตรีไทย - ฆ้องวงเล็ก',
    'ชมรมดนตรีไทย - ปี่ใน',
    'ชมรมดนตรีไทย - ตะโพนไทย',
    'ชมรมดนตรีไทย - กลองแขก',
    'ชมรมดนตรีไทย - ซอด้วง',
    'ชมรมดนตรีไทย - ซออู้',
    'ชมรมดนตรีไทย - ขลุ่ย',
    'ชมรมดนตรีไทย - จะเข้',
    'ชมรมวงดนตรีรวมดาวกระจุย - ขับร้องเพลงไทยลูกทุ่ง',
    'ชมรมวงดนตรีรวมดาวกระจุย - กีตาร์',
    'ชมรมวงดนตรีรวมดาวกระจุย - เบส',
    'ชมรมวงดนตรีรวมดาวกระจุย - คีย์บอร์ด',
    'ชมรมวงดนตรีรวมดาวกระจุย - กลองชุด',
    'ชมรมวงดนตรีรวมดาวกระจุย - เครื่องเป่า Trumpet',
    'ชมรมวงดนตรีรวมดาวกระจุย - เครื่องเป่า Trombone',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - ขับร้องเพลงไทยสากล',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - กีตาร์',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - เปียโน',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - เบส',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - กลองชุด',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - เพอร์คัชชั่น',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - เครื่องเป่า Saxophone',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - เครื่องเป่า Trumpet',
    'ชมรมดนตรีสากล เค.ยู.แบนด์ - เครื่องเป่า Trombone',
    'ชมรมอคูสติก - เพอร์คัชชั่น',
    'ชมรมอคูสติก - ไวโอลิน',
    'ชมรมอคูสติก - วิโอล่า',
    'ชมรมอคูสติก - เชลโล่',
    'ชมรมขับร้องประสานเสียง เค.ยู.คอรัส  - ขับร้องเพลงประสานเสียง',
    'ชมรมขับร้องประสานเสียง เค.ยู.คอรัส  - เปียโน',
    'ชมรมขับร้องประสานเสียง เค.ยู.คอรัส  - คีย์บอร์ด',
    'ชมรมนิสิตอีสาน - พิณ',
    'ชมรมนิสิตอีสาน - โปงลาง',
    'ชมรมนิสิตอีสาน - โหวต',
    'ชมรมนิสิตอีสาน - แคน',
    'ชมรมนาฏศิลป์ไทย - ละครพระ',
    'ชมรมนาฏศิลป์ไทย - ละครนาง',
    'ชมรมโขนละคอน - พระ',
    'ชมรมโขนละคอน - นาง',
    'ชมรมโขนละคอน - ยักษ์',
    'ชมรมโขนละคอน - ลิง',    
]

class CulturalTypeForm(forms.Form):
    cultural_type = forms.ChoiceField(label='กรุณาระบุประเภทศิลปวัฒนธรรม',
                                      choices=zip(ABILITY_CHOICES, ABILITY_CHOICES))

class CulturalExamForm(forms.Form):
    cultural_exam = forms.ChoiceField(label='กรุณาระบุชมรมและสาขาที่ต้องการทดสอบ',
                                      choices=zip(EXAM_CHOICES, EXAM_CHOICES))

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



