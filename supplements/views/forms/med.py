from django import forms

class MedHouseCodesForm(forms.Form):
    applicant_house_code = forms.CharField(label='เลขรหัสประจำบ้านของผู้สมัคร',
                                           max_length=11,
                                           min_length=11,
                                           strip=True,
                                           help_text='กรอกเลขรหัสประจำบ้าน 11 หลัก ไม่ต้องใส่ขีด สามารถดูจากสมุดทะเบียนบ้านของผู้สมัครได้ในทุกหน้า')
    parent_house_code = forms.CharField(label='เลขรหัสประจำบ้านของบิดาหรือมารดาหรือผู้ปกครอง',
                                        max_length=11,
                                        min_length=11,
                                        strip=True,
                                        required=False,
                                        help_text='<b>สำหรับกรณีที่สมัครสาขาแพทย์ศาสตร์</b> กรอกเลขรหัสประจำบ้าน 11 หลัก ไม่ต้องใส่ขีด สามารถดูจากสมุดทะเบียนบ้านของผู้สมัครได้ในทุกหน้า ถ้าสมัครสาขาพยาบาลศาสตร์ไม่ต้องกรอก')

def init_house_codes_form(request,
                          applicant,
                          admission_project,
                          admission_round,
                          form_prefix,
                          current_data):

    if (current_data) and ('applicant_house_code' in current_data):
        initial = {
            'applicant_house_code': current_data['applicant_house_code'],
            'parent_house_code': current_data['parent_house_code'],
        }
        form = MedHouseCodesForm(prefix=form_prefix,
                                 initial=initial)
    else:
        form = MedHouseCodesForm(prefix=form_prefix)

    return {
        'form': form,
    }


def process_house_codes_form(request,
                                 applicant,
                                 admission_project,
                                 admission_round,
                                 form_prefix,
                                 current_data):
    form = MedHouseCodesForm(request.POST, prefix=form_prefix)
    if form.is_valid():
        return (True, {
            'applicant_house_code': form.cleaned_data['applicant_house_code'],
            'parent_house_code': form.cleaned_data['parent_house_code'],
        })
    else:
        return (False, {})

