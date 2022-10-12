from django_bootstrap import bootstrap
bootstrap()

import sys

from regis.models import Applicant
from appl.models import AdmissionProject, AdmissionResult, AdmissionRound, Major


def main():
    project_id = sys.argv[1]
    round_id = sys.argv[2]

    result_filename = sys.argv[3]
    natid_map_filename = sys.argv[4]
    major_map_filename = sys.argv[5]

    if natid_map_filename != '-':
        natid_map = dict([(f[0],f[1]) for f in
                          [l.strip().split(',') for l in
                           open(natid_map_filename).readlines()]])
    else:
        natid_map = None

    major_map = dict([(f[1],f[0]) for f in
                      [l.strip().split(',') for l in
                       open(major_map_filename).readlines()]])

    is_fake = len(sys.argv) <= 6 or (sys.argv[6] != 'real')
    
    admission_project = AdmissionProject.objects.get(pk=project_id)
    admission_round = AdmissionRound.objects.get(pk=round_id)
    project_round = admission_project.get_project_round_for(admission_round)

    majors = dict([(m.number, m) for m in
                   Major.objects.filter(admission_project=admission_project).all()])
    
    result_lines = open(result_filename).readlines()

    mcount = {}
    
    counter = 0
    for line in result_lines:
        items = line.strip().split(',')
        if len(items)!=3:
            continue

        nat_id = items[0].strip()
        major_id = items[1]
        decision = items[2]

        if natid_map != None:
            sys_nat_id = natid_map[nat_id]
        else:
            sys_nat_id = nat_id
            
        major_number = major_map[major_id]

        major = majors[int(major_number)]

        if decision == '1':
            if major.number not in mcount:
                mcount[major.number] = 0
            mcount[major.number] += 1

        try:
            applicant = Applicant.objects.get(national_id=sys_nat_id)
        except:
            print('ERROR', nat_id, sys_nat_id)
            continue
            
        admission_results = AdmissionResult.objects.filter(applicant=applicant,
                                                          major=major).all()
        if len(admission_results)!=1:
            print('ERROR',nat_id,major_id)
            continue

        admission_result = admission_results[0]

        if decision == '1':
            admission_result.is_tcas_confirmed = True
            if not is_fake:
                admission_result.save()
        else:
            admission_result.is_tcas_confirmed = False
            if not is_fake:
                admission_result.save()

        counter += 1
        #print(applicant)

        if counter % 1000 == 0:
            print(counter)


    for num in sorted(majors.keys()):
        if num not in mcount:
            c = 0
        else:
            c = mcount[num]

        print("{0},{1},{2}".format(num,majors[num].title,c))
            
if __name__ == '__main__':
    main()
