from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def read_major_codes(filename):
    majors = {}
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        lines = [l for l in reader]
        for items in lines[1:]:
            if len(items) >= 4:
                majors[items[0]] = {
                    'code': items[0],
                    'name': items[1].strip(),
                    'fac_code': items[2],
                    'ku_code': items[3].strip()
                }
    return majors

def read_app_major_codes(filename):
    app_majors = {}
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        lines = [l for l in reader]
        for items in lines:
            app_majors[int(items[0])] = {
                'app_number': items[0],
                'study_type': items[1].strip(),
                'major_cupt_code': items[2].strip(),
            }
            
    return app_majors

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    app_majors = read_app_major_codes(sys.argv[3])
    major_codes = read_major_codes(sys.argv[4])
    
    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    all_results = AdmissionResult.objects.filter(admission_project=admission_project,
                                             admission_round=admission_round).all()
    
    results = [x[2] for x in sorted([(r.major.number, r.applicant.national_id, r) for r in all_results])]

    count = 0
    for res in results:
        if res.is_accepted:
            count += 1
            applicant = res.applicant
            personal_profile = applicant.get_personal_profile()
            educational_profile = applicant.get_educational_profile()

            application = res.application

            apply_date = application.applied_at.strftime('%d%m') + str(application.applied_at.year + 543)
            apply_time = application.applied_at.strftime('%H%M%S')
            
            major = res.major
            faculty = major.faculty
            campus = faculty.campus
            
            if applicant.has_registered_with_passport():
                national_id = ''
                passport = applicant.passport_number
            else:
                national_id = applicant.national_id
                passport = personal_profile.passport_number

            if applicant.prefix == 'นาย':
                g = 'M'
            else:
                g = 'F'

            app_major_data = app_majors[application.get_number()]
            major_data = major_codes[app_major_data['major_cupt_code']]
            
            study_type_code = {'ภาคปกติ': '1',
                               'ภาคพิเศษ': '2',
                               'นานาชาติ': '3'}[app_major_data['study_type']]
            
            full_major_code = ('002' +
                               admission_project.cupt_code +
                               faculty.cupt_code +
                               app_major_data['major_cupt_code'] +
                               study_type_code)

            full_major_title = ' '.join(['มหาวิทยาลัยเกษตรศาสตร์',
                                         campus.title,
                                         'โครงการ' + admission_project.title,
                                         faculty.title,
                                         major_data['name'].strip(),
                                         '(' + app_major_data['study_type'] + ')'])
            
            items = [count,
                     admission_round.get_full_number(),
                     application.get_number(),
                     national_id,
                     passport,
                     g,
                     applicant.prefix,
                     applicant.first_name,
                     '',
                     applicant.last_name,
                     personal_profile.mobile_phone,
                     personal_profile.contact_phone,
                     educational_profile.school_code,
                     '"%s"' % (educational_profile.school_title,),
                     '002',
                     res.clearing_house_code,
                     'มหาวิทยาลัยเกษตรศาสตร์',
                     campus.short_title,
                     faculty.ku_code,
                     faculty.title,
                     major_data['ku_code'],
                     major.title,
                     admission_project.title,
                     app_major_data['study_type'],
                     full_major_code,
                     full_major_title,
                     apply_date,
                     apply_time,]
            print(','.join([str(i) for i in items]))

if __name__ == '__main__':
    main()
    
