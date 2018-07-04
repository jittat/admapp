from django import forms

class GPAForm(forms.Form):
    science_gpa = forms.FloatField(label='เกรดเฉลี่ยในกลุ่มสาระการเรียนรู้วิทยาศาสตร์',
                                   max_value=4,
                                   min_value=0)
    math_gpa = forms.FloatField(label='เกรดเฉลี่ยในกลุ่มสาระการเรียนรู้คณิตศาสตร์',
                                max_value=4,
                                min_value=0)

def init_gpa_form(request,
                  applicant,
                  admission_project,
                  admission_round,
                  form_prefix,
                  current_data):

    if (current_data) and ('science_gpa' in current_data):
        initial = {
            'science_gpa': current_data['science_gpa'],
            'math_gpa': current_data['math_gpa'],
        }
        form = GPAForm(prefix=form_prefix,
                       initial=initial)
    else:
        form = GPAForm(prefix=form_prefix)
        
    return {
        'form': form,
    }


def process_gpa_form(request,
                     applicant,
                     admission_project,
                     admission_round,
                     form_prefix,
                     current_data):

    form = GPAForm(request.POST, prefix=form_prefix)
    if form.is_valid():
        return (True, {
            'science_gpa': form.cleaned_data['science_gpa'],
            'math_gpa': form.cleaned_data['math_gpa'],
        })
    else:
        return (False, {})

