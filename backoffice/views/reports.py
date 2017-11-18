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

from .projects import load_major_applicants


@user_login_required
def download_applicants_sheet(request, project_id, round_id, major_number):
    user = request.user
    project = get_object_or_404(AdmissionProject, pk=project_id)
    admission_round = get_object_or_404(AdmissionRound, pk=round_id)
    major = Major.get_by_project_number(project, major_number)

    if not can_user_view_applicants_in_major(user, project, major):
        return HttpResponseForbidden()

    filename = 'applicants-{}-{}-{}.csv'.format(project_id, round_id, major_number)
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    writer = csv.writer(response)

    applicants = load_major_applicants(project, admission_round, major)
    writer.writerow(['รหัสประจำตัวประชาชน',
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
                     'การชำระเงินค่าสมัคร',])
    for applicant in applicants:
        if applicant.has_paid:
            payment_message = 'ชำระแล้ว'
        else:
            payment_message = 'ยังไม่ได้ชำระ'
        writer.writerow([applicant.national_id,
                         applicant.personalprofile.passport_number,
                         applicant.prefix,
                         applicant.first_name,
                         applicant.last_name,
                         applicant.email,
                         applicant.personalprofile.contact_phone,
                         applicant.personalprofile.mobile_phone,
                         applicant.educationalprofile.get_education_plan_display(),
                         applicant.educationalprofile.school_title,
                         applicant.educationalprofile.province.title,
                         applicant.educationalprofile.gpa,
                         payment_message,])
    return response


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

def write_applicant_rows(sheet, start_row, applicants, major, cell_format, show_national_id=True):
    faculty = major.faculty
    r = 1
    for applicant in applicants:
        items = [ str(r),
                  applicant.national_id,
                  applicant.prefix,
                  applicant.first_name,
                  applicant.last_name,
                  '%0.2f' % (applicant.educationalprofile.gpa,),
                  applicant.educationalprofile.get_education_plan_display(),
                  faculty.title,
                  major.title,
                  '',
        ]
        if not show_national_id:
            del items[1]
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
                ' มหาวิทยาลัยเกษตรศาสตร์ ปีการศึกษา 2561 (TCAS รอบที่ 1/1)')
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
        
    sheet.write(1,c,'ผลการสัมภาษณ์ (ผ่าน/ไม่ผ่าน/ขาดสอบ)',cell_format)
    sheet.write(2,c,'(กรณีไม่ผ่านโปรดระบุเหตุผล)',cell_format)
        
def write_interview_result_sheet(sheet, project, applicants, major, cell_format):
    sheet.set_landscape()
    sheet.write(0,0,'ใบลงชื่อผู้มีสิทธิ์สอบสัมภาษณ์ โครงการ' +
                project.title +
                ' มหาวิทยาลัยเกษตรศาสตร์ ปีการศึกษา 2561 (TCAS รอบที่ 1/1)')
    set_column_widths(sheet,[4,8,12,22,5,10,12,15,25])
    write_result_table_header(sheet, cell_format)
    write_applicant_rows(sheet, 3, applicants, major, cell_format, False)
    

    count = len(applicants)
    
    sheet.write(count + 5,2,'รวมจำนวนผู้ผ่านสัมภาษณ์ ....................... คน')
    sheet.write(count + 6,2,'ไม่ผ่าน ....................... คน')
    sheet.write(count + 7,2,'ขาดสอบ ....................... คน')
    
    sheet.write(count + 8,6,'ลงชื่อ ................................................. กรรมการสอบสัมภาษณ์')
    sheet.write(count + 9,6,'ลงชื่อ ................................................. กรรมการสอบสัมภาษณ์')
    
    
@user_login_required
def download_applicants_interview_sheet(request, project_id, round_id, major_number):
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
    reg_worksheet = workbook.add_worksheet('ใบลงทะเบียน')
    result_worksheet = workbook.add_worksheet('ใบรายงานผลสัมภาษณ์')
    
    bordered_cell_format = workbook.add_format()
    bordered_cell_format.set_border(1)
    
    applicants = load_major_applicants(project, admission_round, major)

    write_registration_sheet(reg_worksheet, project, applicants, major, bordered_cell_format)
    write_interview_result_sheet(result_worksheet, project, applicants, major, bordered_cell_format)
    
    workbook.close()
    output.seek(0)
    
    filename = 'interview-{}-{}-{}.xlsx'.format(project_id, round_id, major_number)
    response = HttpResponse(output.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

    return response


