from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
from datetime import datetime

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, ProjectApplication

def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    results = AdmissionResult.objects.filter(admission_project=admission_project,
                                             admission_round=admission_round).all()

    

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
            
            if applicant.has_registered_with_passport:
                national_id = ''
                passport = applicant.passport_number
            else:
                national_id = applicant.national_id
                passport = personal_profile.passport_number

            if applicant.prefix == 'นาย':
                g = 'M'
            else:
                g = 'F'
                
            items = [count,
                     admission_round.get_full_number(),
                     res.application.get_number(),
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
                     educational_profile.school_title,
                     '002',
                     res.clearing_house_code,
                     'มหาวิทยาลัยเกษตรศาสตร์',
                     campus.short_title,
                     faculty.ku_code,
                     faculty.title,
                     major.ku_code,
                     major.title,
                     admission_project.title,
                     major.study_type,
                     '',
                     '',
                     apply_date,
                     apply_time,
                     major.number]
            print(','.join([str(i) for i in items]))

if __name__ == '__main__':
    main()
    
