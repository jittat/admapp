import csv
import json
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from regis.models import Applicant, LogItem
from appl.models import AdmissionProject, AdmissionRound
from appl.models import ProjectApplication, Payment, Major, AdmissionResult, Faculty
from appl.models import ProjectUploadedDocument, UploadedDocument

from backoffice.views.permissions import can_user_view_project, can_user_view_applicant_in_major, can_user_view_applicants_in_major
from backoffice.decorators import user_login_required

from .projects import load_major_applicants, load_check_marks_and_results, load_major_applicants_no_cache


def set_column_widths(sheet,widths):
    c = 0
    for w in widths:
        sheet.set_column(c,c,w)
        c += 1

def write_sheet_row(sheet, row, items, cell_format=None):
    c = 0
    for i in items:
        sheet.write(row,c,i,cell_format)
        c += 1


@user_login_required
def download_applicants_sheet(request, project_id, round_id, major_number):
    import xlsxwriter
    import io
    
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    major = Major.get_by_project_number(project, major_number)

    if not can_user_view_applicants_in_major(user, project, major):
        return HttpResponseForbidden()

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    app_worksheet = workbook.add_worksheet('ข้อมูลผู้สมัคร')
    
    bordered_cell_format = workbook.add_format()
    bordered_cell_format.set_border(1)
    
    applicants = load_major_applicants(project, admission_round, major)

    set_column_widths(app_worksheet, [15,8,8,12,22,15,13,13,10,25,10,6,10])
    write_sheet_row(app_worksheet,1,
                    ['รหัสประจำตัวประชาชน',
                     'หมายเลขหนังสือเดินทาง',
                     'คำนำหน้า',
                     'ชื่อต้น',
                     'นามสกุล',
                     'E-mail',
                     'เบอร์โทรที่ติดต่อได้',
                     'เบอร์โทรมือถือ',
                     'แผนการเรียน',
                     'โรงเรียน',
                     'จังหวัด',
                     'GPA',
                     'การชำระเงินค่าสมัคร',],
                    bordered_cell_format)

    r = 2
    for applicant in applicants:
        if applicant.has_paid:
            payment_message = 'ชำระแล้ว'
        else:
            payment_message = 'ยังไม่ได้ชำระ'
        write_sheet_row(app_worksheet, r,
                        [applicant.national_id,
                         applicant.personalprofile.passport_number,
                         applicant.prefix,
                         applicant.first_name,
                         applicant.last_name,
                         applicant.email,
                         applicant.personalprofile.contact_phone,
                         applicant.personalprofile.mobile_phone,
                         str(applicant.educationalprofile.get_education_plan_display()),
                         applicant.educationalprofile.school_title,
                         applicant.educationalprofile.province.title,
                         '%0.2f' % (applicant.educationalprofile.gpa,),
                         payment_message,],
                        bordered_cell_format)
        r += 1

    workbook.close()
    output.seek(0)
    
    filename = 'applicants-{}-{}-{}.xlsx'.format(project_id, round_id, major_number)
    response = HttpResponse(output.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

    return response


def write_applicant_rows(sheet, start_row, applicants, major, cell_format, show_national_id=True):
    faculty = major.faculty
    r = 1
    for applicant in applicants:
        items = [ str(r),
                  applicant.national_id,
                  applicant.prefix,
                  applicant.first_name,
                  applicant.last_name,
                  ('%0.2f' % (applicant.educationalprofile.gpa,)),
                  str(applicant.educationalprofile.get_education_plan_display()),
                  faculty.title,
                  major.title,
                  ' ',
        ]
        if not show_national_id:
            del items[1]
            items.append(' ')
        write_sheet_row(sheet, start_row + r - 1, items, cell_format)
        r += 1


def write_registration_table_header(sheet, cell_format):
    write_sheet_row(sheet,1,
                    ['ลำดับ',
                     'เลขประจำตัวประชาชน',
                     'คำนำหน้า',
                     'ชื่อ',
                     'นามสกุล',
                     'GPAX',
                     'แผนการเรียน',
                     'คณะ',
                     'สาขาวิชา',
                     'ลายมือชื่อ (ตัวบรรจง)',],
                    cell_format)
        
def write_registration_sheet(sheet, project, applicants, major, cell_format):
    sheet.set_landscape()
    sheet.write(0,0,'ใบลงชื่อผู้มีสิทธิ์สอบสัมภาษณ์ โครงการ' +
                project.title +
                ' มหาวิทยาลัยเกษตรศาสตร์ ปีการศึกษา 2561 (TCAS รอบที่ 3)')
    set_column_widths(sheet,[4,15,8,12,22,5,10,12,12,12])
    write_registration_table_header(sheet, cell_format)
    write_applicant_rows(sheet, 2, applicants, major, cell_format)

    count = len(applicants)
    
    sheet.write(count + 4,2,'รวมจำนวนผู้มาสอบสัมภาษณ์ ....................... คน')
    sheet.write(count + 5,2,'ขาดสอบ ....................... คน')
    
    sheet.write(count + 6,6,'ลงชื่อ ................................................. ผู้รับลงทะเบียน')
    sheet.write(count + 7,6,'ลงชื่อ ................................................. ผู้รับลงทะเบียน')
    
    
def write_result_table_header(sheet, cell_format):
    items = ['ลำดับ',
             'คำนำหน้า',
             'ชื่อ',
             'นามสกุล',
             'GPAX',
            'แผนการเรียน',
             'คณะ',
             'สาขาวิชา',]

    c = 0
    for i in items:
        sheet.merge_range(1,c,2,c,i,cell_format)
        c += 1
        
    sheet.write(1,c,'คุณสมบัติ',cell_format)
    sheet.write(2,c,'(ผ่าน/ไม่ผ่าน)',cell_format)
    c+=1
    sheet.write(1,c,'ผลการสัมภาษณ์ (ผ่าน/ไม่ผ่าน/ขาดสอบ)',cell_format)
    sheet.write(2,c,'(กรณีไม่ผ่านโปรดระบุเหตุผล)',cell_format)
        
def write_interview_result_sheet(sheet, project, applicants, major, cell_format):
    sheet.set_landscape()
    sheet.write(0,0,'ใบลงชื่อผู้มีสิทธิ์สอบสัมภาษณ์ โครงการ' +
                project.title +
                ' มหาวิทยาลัยเกษตรศาสตร์ ปีการศึกษา 2561 (TCAS รอบที่ 3)')
    set_column_widths(sheet,[4,8,12,22,5,10,12,15,10,25])
    write_result_table_header(sheet, cell_format)
    write_applicant_rows(sheet, 3, applicants, major, cell_format, False)
    

    count = len(applicants)
    
    sheet.write(count + 5,2,'รวมจำนวนผู้ผ่านสัมภาษณ์ ....................... คน')
    sheet.write(count + 6,2,'ไม่ผ่าน ....................... คน')
    sheet.write(count + 7,2,'ขาดสอบ ....................... คน')
    
    sheet.write(count + 8,6,'ลงชื่อ ................................................. กรรมการสอบสัมภาษณ์')
    sheet.write(count + 9,6,'ลงชื่อ ................................................. กรรมการสอบสัมภาษณ์')

def sorted_by_name(applicants):
    import locale

    locale.setlocale(locale.LC_ALL, 'th_TH.utf8')

    apps = [(locale.strxfrm(a.first_name), locale.strxfrm(a.last_name), a.national_id, a)
            for a
            in applicants]

    results = [x[3] for x in sorted(apps)]
    
    locale.resetlocale()
    
    return results
    
    
@user_login_required
def download_applicants_interview_sheet(request, project_id, round_id, major_number):
    import xlsxwriter
    import io
    
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    major = Major.get_by_project_number(project, major_number)

    if not can_user_view_applicants_in_major(user, project, major):
        return HttpResponseForbidden()

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    reg_worksheet = workbook.add_worksheet('ใบลงทะเบียน')
    result_worksheet = workbook.add_worksheet('ใบรายงานผลสัมภาษณ์')
    
    bordered_cell_format = workbook.add_format()
    bordered_cell_format.set_border(1)
    
    #all_applicants = load_major_applicants(project,
    #                                       admission_round,
    #                                       major,
    #                                       load_results=True)
    
    all_applicants = load_major_applicants_no_cache(project,
                                                    admission_round,
                                                    major)
    load_check_marks_and_results(all_applicants,
                                 project,
                                 admission_round,
                                 project_round)

    applicants = []

    for applicant in all_applicants:
        # HACK
        if not hasattr(applicant,'admission_results'):
            if applicant.admission_result:
                applicant.admission_results = [applicant.admission_result]
            else:
                applicant.admission_results = None
        
        if applicant.admission_results:
            for res in applicant.admission_results:
                if (res.major_id == major.id) and res.is_accepted_for_interview:
                    # HACK for TCAS
                    #if not res.is_tcas_confirmed:
                    #    continue
                        
                    #applicants.append((res.tcas_acceptance_round_number, applicant.national_id, applicant))
                    applicants.append(applicant)

    # HACK
    # applicants = [a[2] for a in sorted(applicants)]
    applicants = sorted_by_name(applicants)
    
    for a in applicants:
        if a.national_id.startswith('T'):
            a.national_id = a.national_id[1:]

    write_registration_sheet(reg_worksheet, project, applicants, major, bordered_cell_format)
    write_interview_result_sheet(result_worksheet, project, applicants, major, bordered_cell_format)
    
    workbook.close()
    output.seek(0)
    
    filename = 'interview-{}-{}-{}.xlsx'.format(project_id, round_id, major_number)
    response = HttpResponse(output.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

    return response


def major_with_udat(major):
    if major.admission_project_id == 13:
        return major.number in [11, 21, 41]
    elif major.admission_project_id == 14:
        return major.number in [6, 30, 33]
    elif major.admission_project_id == 15:
        return major.number == 4
    elif major.admission_project_id == 31:
        return True
    elif major.admission_project_id == 32:
        return major.number in [15,19,70]
    else:
        return False

def major_with_full_onet(major):
    if major.admission_project_id == 32:
        return major.number in [
            33,34,35,36,37,39,40,41,42,43,44,45,46,
            52,53,56,57,58,59,60,61,62,71,
        ]
    else:
        return False

def write_score_report_header(sheet, major, cell_format):
    items = [
        'ลำดับ',
        'เลขประจำตัวประชาชน',
        'คำนำหน้า',
        'ชื่อ',
        'นามสกุล',
        'GPAX',
        'แผนการเรียน',
    ]
    if major_with_full_onet(major):
        items += [
            'O-01',
            'O-02',
            'O-03',
            'O-04',
            'O-05',
        ]
    else:
        items += [
             'ONET(03)',
        ]
    items += [
        'GP-Round',
        'GAT',
        'P1','P2','P3','P4','P5','P6','P7',
    ]
    if major_with_udat(major):
        items += [
            '09',
            '19',
            '29',
            '39',
            '49',
            '59',
            '69',
        ]
    items += ['คะแนนรวม']
    write_sheet_row(sheet,2,
                    items,
                    cell_format)

def write_score_report_sheet(sheet, project, applicants, major, cell_format):
    from backoffice.templatetags.score_extras import score as score_filter
    from backoffice.templatetags.score_extras import score_array as score_array_filter
    from backoffice.templatetags.score_extras import round_array as round_array_filter
    
    sheet.set_landscape()
    set_column_widths(sheet,[3,11,6,9,14,4,8,
                             4,
                             5,5,5,5,5,5,5,5,5,
                             3.5,3.5,3.5,3.5,3.5,3.5,3.5,
                             5])
    sheet.write(0,0,'รายงานคะแนนผู้มีสิทธิ์สอบสัมภาษณ์ โครงการ' + project.title)
    sheet.write(1,0, 'สาขา' + major.title)

    write_score_report_header(sheet, major, cell_format)

    r = 1
    for applicant in applicants:
        scores = applicant.get_all_exam_scores()

        items = [str(r),
                 applicant.national_id,
                 applicant.prefix,
                 applicant.first_name,
                 applicant.last_name,
                 '%0.2f' % (applicant.educationalprofile.gpa,),
                 str(applicant.educationalprofile.get_education_plan_display()),]

        gp_round_count = len(scores.gatpat_rounds)

        if major_with_full_onet(major):
            if hasattr(scores,'onet'):
                items += [
                    score_filter(scores.onet['x01']),
                    score_filter(scores.onet['x02']),
                    score_filter(scores.onet['x03']),
                    score_filter(scores.onet['x04']),
                    score_filter(scores.onet['x05']),
                ]
            else:
                items += [' '] * 5
        else:
            items += [ score_filter(scores.onet['x03']),]

        if hasattr(scores,'gatpat_array'):
            items += [
                round_array_filter(scores.gatpat_rounds, False),
                score_array_filter(scores.gatpat_array['gat'], False),
                score_array_filter(scores.gatpat_array['pat1'], False),
                score_array_filter(scores.gatpat_array['pat2'], False),
                score_array_filter(scores.gatpat_array['pat3'], False),
                score_array_filter(scores.gatpat_array['pat4'], False),
                score_array_filter(scores.gatpat_array['pat5'], False),
                score_array_filter(scores.gatpat_array['pat6'], False),
                round_array_filter(scores.gatpat_array['pat7'], False),
            ]
        else:
            items += [' '] * 9

        if major_with_udat(major):
            if hasattr(scores,'udat'):
                items += [
                    score_filter(scores.udat['u09']),
                    score_filter(scores.udat['u19']),
                    score_filter(scores.udat['u29']),
                    score_filter(scores.udat['u39']),
                    score_filter(scores.udat['u49']),
                    score_filter(scores.udat['u59']),
                    score_filter(scores.udat['u69']),
                ]
            else:
                items += [' '] * 7
        items += [ score_filter(applicant.admission_result.calculated_score) ]

        write_sheet_row(sheet, r + 2, items, cell_format)

        if gp_round_count > 1:
            sheet.set_row(r + 2, gp_round_count * 14)
            
        r += 1


@user_login_required
def download_applicants_interview_score_sheet(request,
                                              project_id,
                                              round_id,
                                              major_number):
    import xlsxwriter
    import io
    
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    project_round = project.get_project_round_for(admission_round)
    major = Major.get_by_project_number(project, major_number)

    if not can_user_view_applicants_in_major(user, project, major):
        return redirect(reverse('backoffice:index'))

    if admission_round.id == 5:
        all_applicants = load_major_applicants(project,
                                               admission_round,
                                               major,
                                               load_results=True)
    else:
        all_applicants = load_major_applicants_no_cache(project,
                                                        admission_round,
                                                        major)    
        load_check_marks_and_results(all_applicants,
                                     project,
                                     admission_round,
                                     project_round)

    applicants = []
    for applicant in all_applicants:
        # HACK
        if not hasattr(applicant,'admission_results'):
            if applicant.admission_result:
                applicant.admission_results = [applicant.admission_result]
            else:
                applicant.admission_results = None
        
        if applicant.admission_results:
            for res in applicant.admission_results:
                if (res.major_id == major.id) and res.is_accepted_for_interview:
                    # HACK for TCAS
                    #if not res.is_tcas_confirmed:
                    #    continue
                        
                    #applicants.append((res.tcas_acceptance_round_number, applicant.national_id, applicant))
                    applicants.append(applicant)

    # HACK
    # applicants = [a[2] for a in sorted(applicants)]
    
    applicants = sorted_by_name(applicants)

    for a in applicants:
        if a.national_id.startswith('T'):
            a.national_id = a.national_id[1:]


    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    score_worksheet = workbook.add_worksheet('คะแนนสอบ')
    
    bordered_cell_format = workbook.add_format()
    bordered_cell_format.set_border(1)
    bordered_cell_format.set_font_size(9)

    write_score_report_sheet(score_worksheet,
                             project,
                             applicants,
                             major,
                             bordered_cell_format)
    workbook.close()
    output.seek(0)

    filename = 'interview-score-{}-{}-{}.xlsx'.format(project_id, round_id, major_number)
    response = HttpResponse(output.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

    return response
