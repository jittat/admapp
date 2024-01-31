from django_bootstrap import bootstrap
bootstrap()

import sys
import json

from appl.models import AdmissionProject, AdmissionRound, ProjectApplication, AdmissionResult

def load_tcas_data(filename):
    lines = open(filename).readlines()

    count = len(lines) // 2

    tcas_data = {}
    
    for i in range(count):
        nat_id = lines[i*2].strip()
        data = json.loads(lines[i*2+1].strip())

        if len(data) == 0:
             tcas_data[nat_id] = { 'status': 'missing' }
             continue

        names = data[0]['studenT_NAME'].split()
        tcas_data[nat_id] = {
            'status': 'found',
            'prefix': names[0],
            'first_name': names[1],
            'last_name': ' '.join(names[2:]), 
        }
        
    return tcas_data

def load_major_map(map_files):
    import csv
    
    major_map = {}
    for f in map_files:
        with open(f) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                project_number = int(row['project'])
                major_number = int(row['number'])
                if project_number not in major_map:
                    major_map[project_number] = {}
                if major_number not in major_map[project_number]:
                    major_map[project_number][major_number] = []

                major_map[project_number][major_number].append(row)
    return major_map

def print_csv_line(applicant, application, personal_profile, app_date, cupt_major,
                   app_type, tcas_id, ranking, applicant_status, interview_description,
                   header):
    university_id = '002'

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

MAJOR_MAP = {
    #1:{
    #    100: [
    #        '10020118620101A,A',
    #        '10020118620101A,B',
    #    ],
    #},
    #2:{
    #    40: ['10020107611106A,'],
    #},
}
    
def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    if (len(sys.argv) >= 4) and (not sys.argv[3].startswith('-')):
        tcas_data_filename = sys.argv[3]
        tcas_data = load_tcas_data(tcas_data_filename)
    else:
        tcas_data = {}

    if (len(sys.argv) >= 5) and (not sys.argv[4].startswith('-')):
        update_json_filename = sys.argv[4]
        update_data = json.loads(open(update_json_filename).read())
    else:
        update_data = {}

    #major_map_files = [f for f in sys.argv[4:] if not f.startswith('--')]
    #major_map = load_major_map(major_map_files)

    major_map = MAJOR_MAP
    
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

    app_type = '1_2567'
    
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
            if nat in tcas_data:
                if tcas_data[nat]['status'] == 'found':
                    is_found = True
                    
                    applicant.prefix = tcas_data[nat]['prefix']
                    applicant.first_name = tcas_data[nat]['first_name']
                    applicant.last_name = tcas_data[nat]['last_name']

            UPDATE_FIELD_MAP = {
                'first_name_th': 'first_name',
                'last_name_th': 'last_name',
                'first_name_en': 'first_name_english',
                'last_name_en': 'last_name_english',
            }
            if nat in update_data:
                for f in update_data[nat]:
                    setattr(applicant, UPDATE_FIELD_MAP[f], update_data[nat][f])
                    
            profile = applicant.get_personal_profile()
            app_date = '%02d/%02d/%04d' % (app.applied_at.day,
                                           app.applied_at.month,
                                           app.applied_at.year + 543)
            
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
                if (project.id in major_map) and (m.number in major_map[project.id]):
                    cupt_majors = []
                    for mj in major_map[project.id][m.number]:
                        cupt_majors.append({
                            'program_id': mj.split(',')[0],
                            'major_id': mj.split(',')[1],
                            'project_id': project.cupt_code,
                        })

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
    
