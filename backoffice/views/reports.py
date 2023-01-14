from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from appl.models import AdmissionProject, AdmissionRound
from appl.models import Major, AdmissionResult
from backoffice.decorators import user_login_required
from backoffice.views.permissions import can_user_view_applicants_in_major
from .projects import load_major_applicants, load_check_marks_and_results, load_major_applicants_no_cache, \
    load_all_judge_comments

ROW_HEIGHT_SCALE = 20

def set_column_widths(sheet,widths):
    c = 0
    for w in widths:
        sheet.set_column(c,c,w)
        c += 1

def write_sheet_row(sheet, row, items,
                    cell_format=None,
                    row_height=None):
    c = 0
    for i in items:
        sheet.write(row,c,i,cell_format)
        c += 1
    if row_height != None:
        sheet.set_row(row, row_height*ROW_HEIGHT_SCALE)

@user_login_required
def download_applicants_sheet(request, project_id, round_id, major_number, only_interview=False):
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
    if only_interview:
        app_worksheet = workbook.add_worksheet('ข้อมูลผู้สมัครที่เรียกสัมภาษณ์')
    else:
        app_worksheet = workbook.add_worksheet('ข้อมูลผู้สมัคร')
    
    bordered_cell_format = workbook.add_format()
    bordered_cell_format.set_border(1)
    
    applicants = load_major_applicants_no_cache(project, admission_round, major)
    load_check_marks_and_results(applicants,
                                 project,
                                 admission_round,
                                 project_round)

    check_mark_cell_formats = [
        workbook.add_format(),
        workbook.add_format(),
        workbook.add_format(),
        workbook.add_format(),
        workbook.add_format(),
        workbook.add_format(),
    ]

    mark_colors = ['blue', 'green', 'yellow', 'red', 'gray', 'black']
    for i in range(6):
        check_mark_cell_formats[i].set_bg_color(mark_colors[i])
        check_mark_cell_formats[i].set_border(1)
    
    set_column_widths(app_worksheet, [15,8,8,12,22,15,13,13,10,25,10,6,12,
                                      2,2,2,2,2,2])

    if only_interview:
        result_header = 'สถานะ'
    else:
        result_header = 'การชำระเงินค่าสมัคร'
    
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
                     result_header,
                     'o',
                     'o',
                     'o',
                     'o',
                     'o',
                     'o',
                     'ความเห็นกรรมการ',
                    ],
                    bordered_cell_format)

    r = 2
    for applicant in applicants:
        if only_interview:
            results = AdmissionResult.objects.filter(applicant=applicant,
                                                    major=major).all()
            if len(results) != 1:
                continue

            result = results[0]
            if not result.is_accepted_for_interview:
                continue
            
            result_message = 'เรียกสัมภาษณ์'
            combined_comments = ''
            row_height = 1
        else:
            if applicant.has_paid:
                result_message = 'ชำระแล้ว'
            else:
                result_message = 'ยังไม่ได้ชำระ'

            comments = load_all_judge_comments(applicant.major_project_application,
                                               project,
                                               admission_round,
                                               major)
            combined_comments = '\n'.join([comment.report_display()
                                           for comment in comments])

            row_height = len([c for c in combined_comments if c == '\n']) + 1
            
        if row_height == 1:
            row_height = None
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
                         '%0.2f' % (float(applicant.educationalprofile.gpa),),
                         result_message,
                         '','','','','','',
                         combined_comments,
                        ],
                        bordered_cell_format,
                        row_height=row_height)
        if (not only_interview) and (applicant.check_marks):
            mcount = 0
            for mark in applicant.check_marks.get_check_mark_list():
                mcount += 1
                if mark['is_checked']:
                    app_worksheet.write(r, 12+mcount,
                                        'o',
                                        check_mark_cell_formats[mcount-1])
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
        nat_id = applicant.national_id
        if nat_id.startswith('x'):
            nat_id = nat_id[1:]
        items = [ str(r),
                  nat_id,
                  applicant.prefix,
                  applicant.first_name,
                  applicant.last_name,
                  '%0.2f' % (float(applicant.educationalprofile.gpa),),
                  str(applicant.educationalprofile.get_education_plan_display()),
                  faculty.title,
                  major.title,
                  ' ',
                  ' '
        ]
        if not show_national_id:
            del items[1]
            items.append(' ')

        items = [str(i) for i in items]
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
                     'ลายมือชื่อ (ตัวบรรจง)',
                     'ยืนยันสิทธิ์',],
                    cell_format)
        
def write_registration_sheet(sheet, project, applicants, major, cell_format):
    sheet.set_landscape()
    sheet.write(0,0,'ใบลงชื่อผู้มีสิทธิ์สอบสัมภาษณ์ โครงการ' +
                project.title +
                ' มหาวิทยาลัยเกษตรศาสตร์ ปีการศึกษา 2564 (TCAS รอบที่ 2)')
    set_column_widths(sheet,[4,15,8,12,22,5,5,10,10,12,12])
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
                ' มหาวิทยาลัยเกษตรศาสตร์ ปีการศึกษา 2564 (TCAS รอบที่ 2)')
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
    
    locale.setlocale(locale.LC_ALL,'POSIX')

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
    MAJORS = {
        11: [12],
        12: [11, 22, 23],
        13: [3, 5, 6, 63],
        14: [2, 3, 45],
        16: [13,14],
        23: [1],
        25: [2],
        31: [25, 26],
    }
    if major.admission_project_id in MAJORS:
        return major.number in MAJORS[major.admission_project_id]
    else:
        return False

def major_with_full_onet(major):
    MAJORS = {
        12: [51],
        13: [61],
        14: [53],
        16: [58, 83],
        31: [8, 21, 24],
    }
    if major.admission_project_id in MAJORS:
        return major.number in MAJORS[major.admission_project_id]
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
    items += [
        'TGAT',
        'TGAT1','TGAT2','TGAT3',
        'TP2',
        'TP21','TP22','TP23',
        'TP3','TP4','TP5'
    ]
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
    sheet.write(0,0,'รายงานคะแนนโครงการ' + project.title)
    sheet.write(1,0, 'สาขา' + major.title)

    write_score_report_header(sheet, major, cell_format)

    r = 1
    for applicant in applicants:
        scores = applicant.get_all_exam_scores()

        nat_id = applicant.national_id
        if nat_id.startswith('x'):
            nat_id = nat_id[1:]
        items = [str(r),
                 nat_id,
                 applicant.prefix,
                 applicant.first_name,
                 applicant.last_name,
                 '%0.2f' % (float(applicant.educationalprofile.gpa),),
                 str(applicant.educationalprofile.get_education_plan_display()),]

        if hasattr(scores,'tgattpat'):
            items += [
                score_filter(scores.tgattpat['tgat']),
                score_filter(scores.tgattpat['tgat1']),
                score_filter(scores.tgattpat['tgat2']),
                score_filter(scores.tgattpat['tgat3']),
                score_filter(scores.tgattpat['tpat2']),
                score_filter(scores.tgattpat['tpat21']),
                score_filter(scores.tgattpat['tpat22']),
                score_filter(scores.tgattpat['tpat23']),
                score_filter(scores.tgattpat['tpat3']),
                score_filter(scores.tgattpat['tpat4']),
                score_filter(scores.tgattpat['tpat5']),
            ]
        else:
            items += [' '] * 11
        #items += [ score_filter(applicant.admission_result.calculated_score) ]
        items += [ "-" ]

        write_sheet_row(sheet, r + 2, items, cell_format)

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


@user_login_required
def download_applicants_score_sheet(request,
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

    applicants = sorted_by_name(all_applicants)

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
