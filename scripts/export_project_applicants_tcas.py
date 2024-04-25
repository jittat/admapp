from django_bootstrap import bootstrap
bootstrap()

import sys
import json

from appl.models import AdmissionProject, AdmissionRound, ProjectApplication, AdmissionResult, PersonalProfile
from regis.models import CuptUpdatedName

def print_csv_line(applicant, application, personal_profile, app_date, cupt_major,
                   app_type, tcas_id, ranking, applicant_status, interview_description,
                   header):
    university_id = '002'

    if personal_profile == None:
        personal_profile = PersonalProfile()
    
    data = {
        'university_id': university_id,
        'program_id': cupt_major['program_id'],
        'major_id': cupt_major['major_id'],
        'project_id': cupt_major['project_id'],
        'type': app_type,
        'citizen_id': '',
        #'gnumber': '',
        #'passport': '',
        'title': applicant.prefix,
        'first_name_th': applicant.first_name,
        'last_name_th': applicant.last_name,
        'first_name_en': personal_profile.first_name_english,
        'last_name_en': personal_profile.last_name_english,
        'priority': 0,
        #'application_id': application.get_number(),
        #'application_date': app_date,
        #'tcas_id': tcas_id,
        'ranking': ranking,
        'score': 0,
        #'interview_status': interview_status,
        #'interview_description': interview_description,
        #'status': 0,
        'tcas_status': 0,
        'applicant_status': applicant_status,
        'interview_reason': '0',
    }

    if not applicant.has_registered_with_passport():
        data['citizen_id'] = applicant.national_id
        #data['first_name_en'] = data['last_name_en'] = ''
    else:
        data['citizen_id'] = applicant.passport_number
        #data['first_name_th'] = data['last_name_th'] = ''
    
    print(','.join(['"'+str(data[h])+'"' for h in header]))


def get_admission_result(application,
                         admission_project,
                         admission_round,
                         major):
    results = AdmissionResult.objects.filter(application=application,
                                             admission_project=admission_project,
                                             admission_round=admission_round,
                                             major=major).all()
    if len(results) == 0:
        return None
    else:
        return results[0]


def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]
    app_type = sys.argv[3]

    if app_type.startswith('-'):
        raise Exception("Error wrong arguments")
    
    only_accepted = False
    if '--accepted' in sys.argv:
        only_accepted = True

    with_applicant_status = False
    if '--applicant_status' in sys.argv:
        with_applicant_status = True

    project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)

    project_applications = ProjectApplication.find_for_project_and_round(project,
                                                                         admission_round,
                                                                         True)

    not_found_list = []

    header = ['university_id',
              'program_id',
              'major_id',
              'project_id',
              'type',
              'citizen_id',
              #'gnumber',
              #'passport',
              'title',
              'first_name_th',
              'last_name_th',
              'first_name_en',
              'last_name_en',
              'priority',
              #'application_id',
              #'application_date',
              #'tcas_id',
              'ranking',
              'score',
              'tcas_status',
              'applicant_status',
              'interview_reason',]

    print(','.join(header))
    
    for app in project_applications:
        if app.has_paid():
            try:
                majors =  app.major_selection.get_majors()
            except:
                majors = []
            applicant = app.applicant
            if applicant.has_registered_with_passport():
                nat = applicant.passport_number
            else:
                nat = applicant.national_id

            is_found = False

            profile = applicant.get_personal_profile()

            app_date = '%02d/%02d/%04d' % (app.applied_at.day,
                                           app.applied_at.month,
                                           app.applied_at.year + 543)

            cupt_updated_names = CuptUpdatedName.objects.filter(applicant=applicant).all()
            for updated_name in cupt_updated_names:
                updated_name.apply_update(applicant, profile)
            
            for m in majors:
                result = None
                
                if only_accepted:
                    result = get_admission_result(app, project, admission_round, m)
                    if (not result) or (not result.is_accepted):
                        continue

                    
                cupt_majors = [{
                    'program_id': m.get_detail_items()[-2],
                    'major_id': m.get_detail_items()[-1],
                    'project_id': project.cupt_code,
                }]

                if len(cupt_majors[0]['major_id']) > 10:
                    cupt_majors[0]['program_id'] = cupt_majors[0]['major_id']
                    cupt_majors[0]['major_id'] = ''
                
                applicant_status = '1'
                if with_applicant_status:
                    if not result:
                        result = get_admission_result(app, project, admission_round, m)

                    if result and result.is_accepted:
                        applicant_status = '2'
                    else:
                        applicant_status = '3'
                
                for cupt_major in cupt_majors:
                    print_csv_line(applicant, app, profile,
                                   app_date, cupt_major,
                                   app_type,
                                   '0','0',
                                   applicant_status,
                                   '0',
                                   header)

if __name__ == '__main__':
    main()
    
