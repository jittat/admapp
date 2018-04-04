from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionRound, Payment, AdmissionProjectRound, ProjectApplication

import xlsxwriter
import io

MAX_ROWS = 5000

def compute_amount_paid(admission_round):
    payments = Payment.objects.filter(admission_round=admission_round).all()

    amount_paid = {}
    for p in payments:
        if p.applicant == None:
            continue
        nat_id = p.applicant.national_id
        if nat_id not in amount_paid:
            amount_paid[nat_id] = p.amount
        else:
            amount_paid[nat_id] += p.amount

    return amount_paid


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

def write_applicant(sheet, row, applicant, counter):
    write_sheet_row(sheet, row,
                    [counter,
                     int(applicant.national_id),
                     applicant.prefix,
                     applicant.first_name,
                     applicant.last_name])
                     
        
def write_applicants(filename, applicants, base_counter):
    workbook = xlsxwriter.Workbook(filename)
    app_worksheet = workbook.add_worksheet('Applicants')
    set_column_widths(app_worksheet,[12.5, 19.332, 8.832, 13.164, 8.832])
    write_sheet_row(app_worksheet,0,
                    ['เลขเรียงลำดับ',
                     'เลขประจำตัวประชาชน',
                     'คำนำหน้า',
                     'ชื่อ',
                     'นามสกุล'])

    c = 0
    for app in applicants:
        c += 1
        cnt = base_counter + c
        write_applicant(app_worksheet, c, app, cnt)
        
    workbook.close()
    
        
def main():
    round_id = sys.argv[1]
    base_excel_filename = sys.argv[2]

    admission_round = AdmissionRound.objects.get(pk=round_id)
    amount_paid = compute_amount_paid(admission_round)

    project_rounds = AdmissionProjectRound.objects.filter(admission_round=admission_round)
    all_applicants = {}
    
    for pr in project_rounds:
        admission_project = pr.admission_project
    
        project_applicants = ProjectApplication.objects.filter(admission_project=admission_project,
                                                               admission_round=admission_round).all()

    
        for app in project_applicants:
            national_id = app.applicant.national_id
            if national_id in amount_paid:
                if national_id not in all_applicants:
                    all_applicants[national_id] = app.applicant

    print('Total', len(all_applicants))

    applicants = list(all_applicants.values())

    left = applicants
    counter = 0
    while len(left) > 0:
        counter += 1
        write_applicants("%s-%d.xlsx" % (base_excel_filename, counter),
                         left[:MAX_ROWS],
                         (counter - 1) * MAX_ROWS)
        left = left[MAX_ROWS:]
    
if __name__ == '__main__':
    main()
    
