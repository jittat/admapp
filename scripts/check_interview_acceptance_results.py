from django_bootstrap import bootstrap
bootstrap()
import sys

from appl.models import Major, AdmissionRound, AdmissionProject, AdmissionProjectRound, MajorInterviewDescriptionCache, AdmissionResult
from backoffice.models import (
    InterviewDescription,
    AdmissionProjectMajorCuptCodeInterviewDescription,
)

def main():
    admission_round = AdmissionRound.objects.get(pk=sys.argv[1])

    interview_descriptions = InterviewDescription.objects.filter(admission_round=admission_round).order_by('-id')

    major_map = { i.major_id:i for i in interview_descriptions }

    projects = admission_round.get_available_projects()

    majors = []
    for p in projects:
        majors += list(p.major_set.all())

    faculty_project_majors = {}
    for m in majors:
        k = (m.faculty_id, m.admission_project_id)
        if k not in faculty_project_majors:
            faculty_project_majors[k] = []
        faculty_project_majors[k].append(m)

    major_cupt_full_code_map = {}
    for m in majors:
        if m.cupt_full_code not in major_cupt_full_code_map:
            major_cupt_full_code_map[m.cupt_full_code] = []
        major_cupt_full_code_map[m.cupt_full_code].append(m)

        
    for m in majors:
        m.spanned_interview_descriptions = []
        if m.id in major_map:
            m.interview_description = major_map[m.id]
        else:
            m.interview_description = None

    # span individually
    for i in interview_descriptions:
        if i.span_option == InterviewDescription.OPTION_SPAN_INDIVIDUAL:
            for project_cupt_code_description in AdmissionProjectMajorCuptCodeInterviewDescription.objects.filter(interview_description=i):
                cupt_full_code = project_cupt_code_description.major_cupt_code.get_program_major_code_as_str()
                for m in major_cupt_full_code_map[cupt_full_code]:
                    if m.admission_project_id == project_cupt_code_description.admission_project_id:
                        m.spanned_interview_descriptions.append(i)
                        
    # spans same code
    for i in interview_descriptions:
        if i.span_option == InterviewDescription.OPTION_SPAN_SAME_CUPT_CODE:
            interview_major = i.major
            for m in major_cupt_full_code_map[interview_major.cupt_full_code]:
                m.spanned_interview_descriptions.append(i)

    # spans same project
    for i in interview_descriptions:
        if i.span_option == InterviewDescription.OPTION_SPAN_SAME_PROJECT:
            k = (i.faculty_id, i.admission_project_id)
            if k in faculty_project_majors:
                for m in faculty_project_majors[k]:
                    m.spanned_interview_descriptions.append(i)

    for m in majors:
        if not m.interview_description:
            if len(m.spanned_interview_descriptions) > 0:
                m.interview_description = m.spanned_interview_descriptions[0]
                    
    for m in majors:
        if not m.interview_description:
            continue

        interview_description = m.interview_description
        if interview_description.interview_options == InterviewDescription.OPTION_NO_INTERVIEW:
            pass
        else:
            results = AdmissionResult.objects.filter(major=m, is_accepted_for_interview=True).all()
            counters = {'accepted':0, 'rejected':0, 'missed':0, 'none':0}
            for r in results:
                if r.is_interview_absent == True:
                    counters['missed'] += 1
                elif r.is_accepted:
                    counters['accepted'] += 1
                elif r.is_accepted == False:
                    counters['rejected'] += 1
                else:
                    counters['none'] += 1
            if counters['none'] > 0:
                print(m, counters)

if __name__ == '__main__':
    main()
