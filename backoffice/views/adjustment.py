import csv
import json
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from regis.models import Applicant, LogItem
from appl.models import Faculty, AdmissionRound
from backoffice.models import AdjustmentMajor, AdjustmentMajorSlot

from backoffice.decorators import number_adjustment_login_required

from backoffice.views.permissions import can_user_adjust_major, can_user_confirm_major_adjustment

def load_faculty_major_statistics(faculty, admission_rounds):
    adjustment_majors = (AdjustmentMajor.objects.
                         filter(faculty=faculty).order_by('full_code').all())

    mmap = {}
    for m in adjustment_majors:
        m.round_stats = []
        for i in admission_rounds:
            m.round_stats.append([0,-1])
        m.all_confirmed = True
        mmap[m.full_code] = m

    for slot in AdjustmentMajorSlot.objects.filter(faculty=faculty).all():
        m = mmap[slot.major_full_code]
        m.round_stats[slot.admission_round_number - 1][0] += slot.current_slots
        if slot.is_editable():
            m.all_confirmed = False
        if slot.is_final:
            if m.round_stats[slot.admission_round_number - 1][1] == -1:
                m.round_stats[slot.admission_round_number - 1][1] = 0
            m.round_stats[slot.admission_round_number - 1][1] += slot.confirmed_slots
        
    return adjustment_majors

@number_adjustment_login_required
def index(request):
    user = request.user
    
    if user.is_super_admin:
        faculties = Faculty.objects.all()
        can_confirm = True
    else:
        faculties = [user.profile.faculty]
        can_confirm = user.profile.major_number == 0

    admission_rounds = [r for r in AdmissionRound.objects.all()
                        if r.subround_number != 2]
    
    for f in faculties:
        f.majors = load_faculty_major_statistics(f, admission_rounds)

    notice = request.session.pop('notice','')
        
    return render(request,
                  'backoffice/adjustment/index.html',
                  { 'faculties': faculties,
                    'admission_rounds': admission_rounds,

                    'can_confirm': can_confirm,
                    
                    'notice': notice })

def validate_updated_number(slot, number):
    try:
        num = int(number)
    except:
        return False, 'ต้องเป็นตัวเลข'
    if num < slot.original_slots:
        return False, 'ต้องไม่ลดลงจากแผน'
    return True, ''

@number_adjustment_login_required
def major_index(request, major_full_code):
    major = get_object_or_404(AdjustmentMajor, full_code=major_full_code)

    if not can_user_adjust_major(request.user, major):
        return redirect(reverse('backoffice:adjustment'))

    admission_rounds = AdmissionRound.objects.all()
    
    major_slots = major.slots.all()

    notice = ''
    validation_error = False

    can_confirm = can_user_confirm_major_adjustment(request.user, major)
    save_and_confirm = False
    
    if request.method == 'POST':
        if 'cancel' in request.POST:
            request.session['notice'] = 'ยกเลิกการแก้ไข ' + major.title + 'เรียบร้อย'
            return redirect(reverse('backoffice:adjustment'))

        if 'saveconfirm' in request.POST:
            if can_confirm:
                save_and_confirm = True
        
        slots = [s for s in major_slots
                 if s.is_editable()]

        updated_slots = []
        for s in slots:
            key = 'slot-%s-%s' % (s.id, s.cupt_code)
            if key in request.POST:
                new_slot = request.POST[key].strip()
                ok, msg = validate_updated_number(s, new_slot)
                if ok:
                    s.current_slots = int(new_slot)
                    s.validation_error = False
                    updated_slots.append(s)
                else:
                    s.current_slots = new_slot
                    validation_error = True
                    s.validation_error = True
                    s.validation_error_msg = msg
                    
        if not validation_error:
            for s in updated_slots:
                if save_and_confirm:
                    s.is_confirmed_by_faculty = True
                s.save()
                    
            notice = 'สามารถจัดเก็บได้เรียบร้อย'

            slot_msg = ','.join(['%d:%d' % (s.id, s.current_slots)
                                 for s in updated_slots])
            
            if 'savereturn' in request.POST:
                request.session['notice'] = 'จัดเก็บการแก้ไข ' + major.title + ' เรียบร้อย'
                LogItem.create('Save major {0} slots {1}'.format(major.full_code, slot_msg),
                               request=request)

                return redirect(reverse('backoffice:adjustment'))

            if save_and_confirm:
                request.session['notice'] = 'จัดเก็บและยืนยันจำนวนรับ ' + major.title + ' เรียบร้อย'
                LogItem.create('Save and confirm major {0} slots {1}'.format(major.full_code, slot_msg),
                               request=request)

                return redirect(reverse('backoffice:adjustment'))

    any_editable = len([s for s in major_slots if s.is_editable()]) != 0
    
    return render(request,
                  'backoffice/adjustment/major_index.html',
                  { 'major': major,
                    'major_slots': major_slots,
                    'faculty': major.faculty,
                    'admission_rounds': admission_rounds,

                    'any_editable': any_editable,
                    'can_confirm': can_confirm,
                    
                    'validation_error': validation_error,
                    'notice': notice })

