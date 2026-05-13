from django_bootstrap import bootstrap
bootstrap()

import sys
import csv

from regis.models import Applicant 
from appl.models import ProjectApplication, School, AdmissionResult, Payment, AdmissionRound, MajorSelection
from appl.models import PersonalProfile, EducationalProfile

from thefuzz import fuzz

def get_projects(admission_rounds):
    return sum([list(r.get_available_projects()) for r in admission_rounds], [])

def get_results():
    results = {}
    for r in AdmissionResult.objects.all():
        if r.applicant_id not in results:
            results[r.applicant_id] = []
        results[r.applicant_id].append(r)
    return results

APPLYING = 1
ACCEPTED = 2
CONFIRMED = 3

def update_applicant_statuses(applicants, results):
    for i in applicants:
        ap = applicants[i]
        if ap.id not in results:
            ap.adm_type = APPLYING
            continue

        ac = False
        cf = False
        for r in results[ap.id]:
            if r.is_accepted:
                ac = True
                if r.has_confirmed:
                    cf = True
        if cf:
            ap.adm_type = CONFIRMED
        elif ac:
            ap.adm_type = ACCEPTED
        else:
            ap.adm_type = APPLYING


def normalize_school_title(title):
    title = title.replace(" ","")
    title = title.replace("เเ","แ")
    if title.startswith("โรงเรียน"):
        title = title.replace("โรงเรียน", "")
    if title.startswith("โรงรียน"):
        title = title.replace("โรงรียน", "")
    if title.startswith("รร."):
        title = title.replace("รร.", "")
    nummap = {
        "๐": "0",
        "๑": "1",
        "๒": "2",
        "๓": "3",
        "๔": "4",
        "๕": "5",
        "๖": "6",
        "๗": "7",
        "๘": "8",
        "๙": "9",
    }
    for n in nummap:
        title = title.replace(n, nummap[n])
    return title

def map_school_codes(applicants, edu_profiles, school_map):
    province_schools = {}
    for scode in school_map:
        school = school_map[scode]
        school.normalized_title = normalize_school_title(school.title)
        if school.province_id not in province_schools:
            province_schools[school.province_id] = []
        province_schools[school.province_id].append(school)


    for i in applicants:
        ap = applicants[i]
        e = edu_profiles[ap.id]
        if e.school_code != '':            
            e.school_province = school_map[e.school_code].province
        else:
            normalized_title = normalize_school_title(e.school_title)
            province_id = e.province_id

            not_found = True
            if province_id in province_schools:
                for s in province_schools[province_id]:
                    if s.normalized_title == normalized_title:
                        e.school_code = s.code
                        e.school_province = s.province
                        not_found = False
                        break

                if not_found:
                    for s in province_schools[province_id]:
                        if fuzz.ratio(s.normalized_title,normalized_title) > 90:
                            print(f"Mapping {normalized_title} to {s.normalized_title}")
                            e.school_code = s.code
                            e.school_province = s.province
                            not_found = False
                            break

            if not_found:
                print(f"Not found: {e.school_title} -> {normalized_title}")
                e.school_code = e.school_title
                e.school_province = e.province



def main():
    output_filename = sys.argv[2]
    round_ids = [int(r) for r in sys.argv[1].split(",")]
    admission_rounds = [AdmissionRound.objects.get(pk=r) for r in round_ids]
    projects = get_projects(admission_rounds)

    applicants = {}
    for a in ProjectApplication.objects.filter(admission_round__in=admission_rounds,
                                               is_canceled=False,
                                               cached_has_paid=True).select_related('applicant').all():
        applicants[a.applicant_id] = a.applicant

    results = get_results()
    update_applicant_statuses(applicants, results)

    c=[0,0,0,0]
    for i in applicants:
        a = applicants[i]
        c[a.adm_type] += 1
    print(c[1:])

    per_profiles = {p.applicant_id:p for p in PersonalProfile.objects.all()}
    edu_profiles = {e.applicant_id:e for e in EducationalProfile.objects.all()}
    school_map = {s.code:s for s in School.objects.all()}

    map_school_codes(applicants, edu_profiles, school_map)

    stats = {}
    for t in [1,2,3]:
        for i in applicants:
            ap = applicants[i]
            if ap.adm_type < t:
                continue
                
            e = edu_profiles[ap.id]
            scode = e.school_code
                
            if scode not in stats:
                stats[scode] = {
                    'title': e.school_title,
                    'province': e.school_province,
                    'count-1': 0,
                    'total-1': 0,
                    'count-2': 0,
                    'total-2': 0,
                    'count-3': 0,
                    'total-3': 0,
                }
            stats[scode][f'count-{t}'] += 1
            stats[scode][f'total-{t}'] += e.gpa

    for t in [1,2,3]:    
        for s in stats:
            if stats[s][f'count-{t}'] != 0:
                stats[s][f'avr-{t}'] = stats[s][f'total-{t}'] / stats[s][f'count-{t}']
            else:
                stats[s][f'avr-{t}'] = ''

    with open(output_filename,'w') as f:
        writer = csv.writer(f)
        writer.writerow(['code','title','province','apply','apply-avr-gpa','accept','accept-avr-gpa','confirm','confirm-avr-gpa'])
        for s in stats:
            ss = stats[s]
            writer.writerow([s,ss['title'],
                            ss['province'],
                            ss['count-1'],ss['avr-1'],
                            ss['count-2'],ss['avr-2'],
                            ss['count-3'],ss['avr-3'],
                            ])

if __name__ == "__main__":
    main()