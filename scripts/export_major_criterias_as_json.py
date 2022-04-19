from django_bootstrap import bootstrap
bootstrap()

import sys
import csv
import json
import copy
from datetime import datetime

import yaml
    
from appl.models import AdmissionProject, AdmissionRound, Faculty
from criteria.models import AdmissionCriteria

error_report_file = sys.stderr

SCORE_TYPE_TAG_FILENAME = 'score_type_tags.yaml'

FIELDS = [
    'min_r4_total_score',
    'min_gpax',
    'min_credit_gpa21',
    'min_credit_gpa22',
    'min_credit_gpa23',
    'min_credit_gpa24',
    'min_credit_gpa25',
    'min_credit_gpa26',
    'min_credit_gpa27',
    'min_credit_gpa28',
    'min_gpa21',
    'min_gpa22',
    'min_gpa23',
    'min_gpa24',
    'min_gpa25',
    'min_gpa26',
    'min_gpa27',
    'min_gpa28',
    'min_onet',
    'min_onet01',
    'min_onet02',
    'min_onet03',
    'min_onet04',
    'min_onet05',
    'min_gat',
    'min_gat1',
    'min_gat2',
    'min_pat1and2',
    'min_pat1',
    'min_pat2',
    'min_pat3',
    'min_pat4',
    'min_pat5',
    'min_pat6',
    'min_pat7_1',
    'min_pat7_2',
    'min_pat7_3',
    'min_pat7_4',
    'min_pat7_5',
    'min_pat7_6',
    'min_pat7_7',
    'min_9sub_09',
    'min_9sub_19',
    'min_9sub_29',
    'min_9sub_39',
    'min_9sub_49',
    'min_9sub_59',
    'min_9sub_69',
    'min_9sub_89',
    'min_9sub_99',
    'min_vnet_51',
    'min_vnet_511',
    'min_vnet_512',
    'min_vnet_513',
    'min_vnet_514',
    'min_bnet_393',
    'min_bnet_394',
    'min_inet_31',
    'min_inet_33',
    'min_inet_35',
    'min_inet_38',
    'min_nnet_421',
    'min_nnet_422',
    'min_nnet_423',
    'min_nnet_424',
    'min_nnet_425',
    'min_toefl_ibt',
    'min_toefl_pbt',
    'min_toefl_cbt',
    'min_toefl_ipt',
    'min_ielts',
    'min_toeic',
    'min_cutep',
    'min_tuget',
    'min_kept',
    'min_psutep',
    'min_kuept',
    'min_cmuetegs',
    'min_sat',
    'min_cefr  ',
    'min_ged_score',
    'min_gpa22_23',
]

COMPONENT_WEIGHT_OPTIONS = [
    ('CW110','1.1',0),
    ('CW120','1.2',0),
    ('CW130','1.3',0),
    ('CW140','1.4',0),
    ('CW210','2.1',0),
    ('CW220','2.2',0),
    ('CW300','3',0),
    ('CW400','4',0),
    ('CW500','5',0),
    ('CW610','6.1',0),
    ('CW621','6.2.1',0),
    ('CW62271','6.2.2','PAT7.1'),
    ('CW62272','6.2.2','PAT7.2'),
    ('CW62273','6.2.2','PAT7.3'),
    ('CW62274','6.2.2','PAT7.4'),
    ('CW62275','6.2.2','PAT7.5'),
    ('CW62276','6.2.2','PAT7.6'),
    ('CW62277','6.2.2','PAT7.7'),
    ('CW701','7.1',0),
    ('CW7021','7.2','PAT1'),
    ('CW7022','7.2','PAT2'),
    ('CW7023','7.2','PAT3'),
    ('CW7024','7.2','PAT4'),
    ('CW7026','7.2','PAT6'),
    ('CW70271','7.2','PAT7.1'),
    ('CW70272','7.2','PAT7.2'),
    ('CW70273','7.2','PAT7.3'),
    ('CW70274','7.2','PAT7.4'),
    ('CW70275','7.2','PAT7.5'),
    ('CW70276','7.2','PAT7.6'),
    ('CW70277','7.2','PAT7.7'),
    ('CW8004','8','PAT4'),
    ('CW8006','8','PAT6'),
    ('CW910','9.1',0),
    ('CW921','9.2.1',0),
    ('CW92271','9.2.2','PAT7.1'),
    ('CW92272','9.2.2','PAT7.2'),
    ('CW92273','9.2.2','PAT7.3'),
    ('CW92274','9.2.2','PAT7.4'),
    ('CW92275','9.2.2','PAT7.5'),
    ('CW92276','9.2.2','PAT7.6'),
    ('CW92277','9.2.2','PAT7.7'),
]

COMPONENT_WEIGHT_MAP = { c[0]:(c[1],c[2]) for c in COMPONENT_WEIGHT_OPTIONS }

SCORE_TYPE_REVERSE_MAP = {}
PROJECT_SCORE_TYPE_REVERSE_MAP = {}

def find_score_type_from_str(st, reverse_map):
    st = st.strip()
    st_no_space = st.replace(" ","")
    st_norm_space = ' '.join(st.split())
    if st_no_space in reverse_map:
        return reverse_map[st_no_space]
    elif st_norm_space in reverse_map:
        return reverse_map[st_norm_space]
    else:
        return 'OTHER'

    
def load_score_type_tags(filename):

    def add_score_tags(output_tags, r):
        if 'description' in r:
            output_tags.append(r)
        elif 'descriptions' in r:
            for desc in r['descriptions']:
                new_tag = r.copy()
                del new_tag['descriptions']
                new_tag['description'] = desc
                output_tags.append(new_tag)

    def build_map(tags):
        return dict([
            (t['description'].strip(), t['score_type'].strip())
            for t in tags
        ])

                
    global SCORE_TYPE_REVERSE_MAP
    global PROJECT_SCORE_TYPE_REVERSE_MAP
    
    try:
        from yaml import CLoader as Loader, CDumper as Dumper
    except ImportError:
        from yaml import Loader, Dumper

    raw_tags = yaml.load(open(filename).read(), Loader=Loader)
    output_tags = []
    project_tags = {}
    
    for r in raw_tags:
        if 'project_id' in r:
            if r['project_id'] not in project_tags:
                project_tags[r['project_id']] = []
            for rr in r['score_tags']:
                add_score_tags(project_tags[r['project_id']], rr)
        else:
            add_score_tags(output_tags, r)

    SCORE_TYPE_REVERSE_MAP = build_map(output_tags)
    for k in project_tags:
        PROJECT_SCORE_TYPE_REVERSE_MAP[k] = build_map(project_tags[k])

load_score_type_tags(SCORE_TYPE_TAG_FILENAME)

SCORE_TYPE_FIELD_MAP = {
    "GPAX_5_SEMESTER": 'ERROR',
    "GPAX": "min_gpax",
    "UNIT_MATH": 'min_credit_gpa22',
    "UNIT_FOREIGN": 'min_credit_gpa28',
    "UNIT_SCI": 'min_credit_gpa23',
    "ONET": 'min_onet',
    "ONET_THA": 'min_onet01',
    "ONET_SOC": 'min_onet02',
    "ONET_ENG": 'min_onet03',
    "ONET_MAT": 'min_onet04',
    "ONET_SCI": 'min_onet05',
    "GAT": 'min_gat',
    "GAT_1": 'min_gat1',
    "GAT_2": 'min_gat2',
    "PAT_1": 'min_pat1',
    "PAT_2": 'min_pat2',
    "PAT_3": 'min_pat3',
    "PAT_4": 'min_pat4',
    "PAT_5": 'min_pat5',
    "PAT_6": 'min_pat6',
    "PAT_7_1": 'min_pat7_1',
    "PAT_7_2": 'min_pat7_2',
    "PAT_7_3": 'min_pat7_3',
    "PAT_7_4": 'min_pat7_4',
    "PAT_7_5": 'min_pat7_5',
    "PAT_7_6": 'min_pat7_6',
    "PAT_7_7": 'min_pat7_7',
    "UDAT_09": 'min_9sub_09',
    "UDAT_19": 'min_9sub_19',
    "UDAT_29": 'min_9sub_29',
    "UDAT_39": 'min_9sub_39',
    "UDAT_49": 'min_9sub_49',
    "UDAT_59": 'min_9sub_59', 
    "UDAT_69": 'min_9sub_69',
    "UDAT_89": 'min_9sub_89',
    "UDAT_99": 'min_9sub_99',

    "MIN_GPA21": 'min_gpa21',
    "MIN_GPA22": 'min_gpa22',
    "MIN_GPA23": 'min_gpa23',
    "MIN_GPA28": 'min_gpa28',
}

def print_error(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)

def reverse_score_type(score_criteria, curriculum_major):
    if score_criteria.score_type != 'OTHER':
        return score_criteria.score_type
    else:
        description = score_criteria.description.strip()
        if curriculum_major.admission_project_id in PROJECT_SCORE_TYPE_REVERSE_MAP:
            score_type = find_score_type_from_str(description, PROJECT_SCORE_TYPE_REVERSE_MAP[curriculum_major.admission_project_id])
            if score_type != 'OTHER':
                return score_type
        
        score_type = find_score_type_from_str(score_criteria.description.strip(), SCORE_TYPE_REVERSE_MAP)
        if score_type != 'OTHER':
            return score_type
        else:
            return 'OTHER'

all_missing_descriptions = []
    
def min_score_vector_from_criterias(score_criterias, curriculum_major):
    value_vectors = {}
    for f in FIELDS:
        if f.startswith('min') or f.startswith('max'):
            value_vectors[f] = 0

    if score_criterias == []:
        return value_vectors
            
    is_error = False
    for c in score_criterias:
        score_type = c.score_type
        if score_type == 'OTHER':
            score_type = reverse_score_type(c, curriculum_major)
        if c.value != None and c.value > 0:
            if score_type == 'IGNORE':
                continue
            if score_type not in SCORE_TYPE_FIELD_MAP:
                print_error(f'Error missing {score_type} {c} "{c.description.strip()}"')
                all_missing_descriptions.append(c.description)
                is_error = True
            elif SCORE_TYPE_FIELD_MAP[score_type] == 'ERROR':
                #print_error('Found:', score_type, c)
                print_error('Error gpax5', c)
                is_error = True
            else:
                value_vectors[SCORE_TYPE_FIELD_MAP[score_type]] = float(c.value)
        else:
            if score_type == 'OTHER':
                is_error = True
                print_error(f'OTHER - None: Error missing {score_type} {c} "{c.description.strip()}" [{c.value}]')

    if is_error:
        print_error('=============', curriculum_major.faculty, '==========', curriculum_major.cupt_code)
                
    return value_vectors

def min_score_vectors(admission_criteria, curriculum_major):
    if not admission_criteria:
        return [min_score_vector_from_criterias([], curriculum_major)]

    or_count = 0
    or_criterias = []
    
    is_error = False
    score_criterias = []
    for c in admission_criteria.get_all_required_score_criteria():
        if c.has_children():
            if c.relation != 'AND':
                if c.relation == 'OR':
                    or_count += 1
                    for child in c.childs.all():
                        or_criterias.append(child)
                if (or_count > 1) or (c.relation != 'OR'):
                    print_error('Error type (or too many OR):', c.relation)
                    for child in c.childs.all():
                        print_error(f"    - {child}")
                    is_error = True
            else:
                for child in c.childs.all():
                    score_criterias.append(child)
        else:
            score_criterias.append(c)        

    if or_count == 0:
        value_vectors = min_score_vector_from_criterias(score_criterias, curriculum_major)
    
        if is_error:
            print_error('=============', curriculum_major.faculty, '==========', curriculum_major.cupt_code)
                
        return [value_vectors]
    elif or_count == 1:
        print_error('OR found:', or_criterias)
        output = []
        for or_criteria in or_criterias:
            this_score_criterias = [c for c in score_criterias] + [or_criteria]
            
            value_vectors = min_score_vector_from_criterias(this_score_criterias, curriculum_major)

            output.append(value_vectors)
            
        if is_error:
            print_error('=============', curriculum_major.faculty, '==========', curriculum_major.cupt_code)

        return output

    else:
        value_vectors = min_score_vector_from_criterias(score_criterias, curriculum_major)
    
        if is_error:
            print_error('TOO MANY ORs =============', curriculum_major.faculty, '==========', curriculum_major.cupt_code)
                
        return [value_vectors]


def update_component_weight(row, admission_criteria, curriculum_major):
    score_criterias = []
    is_error = False
    is_assigned = False
    
    for c in admission_criteria.get_all_scoring_score_criteria():
        if c.has_children():
            print_error('Error type:', c.relation)
            for child in c.childs.all():
                print(f"    - {child}")
                is_error = True
        else:
            score_criterias.append(c)        

    if len(score_criterias) != 1:
        print_error('Too many', len(score_criterias))
        is_error = True
        
    for c in score_criterias:
        score_type = c.score_type
        if score_type == 'OTHER':
            score_type = reverse_score_type(c, curriculum_major)

        if score_type in COMPONENT_WEIGHT_MAP:
            cw, cpat = COMPONENT_WEIGHT_MAP[score_type]
            row['component_weight'] = cw
            row['component_pat'] = cpat
            is_assigned = True
        else:
            print_error('Unknown scoring', c)
            is_error = True

    if not is_assigned:
        print_error('ERROR not assigned')
        
    if is_error or (not is_assigned):
        print_error("----------------", curriculum_major.cupt_code)

def fix_score_type(c, curriculum_major):
    if c.score_type == 'OTHER':
        c.score_type = reverse_score_type(c, curriculum_major)
        
def score_vector_from_criterias(admission_criteria, curriculum_major):
    is_error = False
    
    print_error(f"-------------- {curriculum_major.cupt_code} --------------")
    score_criterias = []

    child_values = []
    for c in admission_criteria.get_all_scoring_score_criteria():
        if c.value == 0:
            if 'สัมภา' not in c.description:
                c.value = 1
        if c.has_children():
            if c.relation == 'SUM':
                child_total = sum([child.value for child in c.childs.all()])
            elif c.relation == 'MAX':
                child_total = 1
            else:
                print_error('**** ERROR bad relation', curriculum_major, c.relation)
                child_total = 0
            if child_total == 0:
                # print('*** CHILD ERROR *** total = 0', curriculum_major)
                child_total = 1
            child_values.append(child_total)
            c.child_total_values = child_total
        else:
            child_values.append(1)
            c.child_total_values = 1

    total_weight_scale = 1
    for v in child_values:
        total_weight_scale *= v

    main_total = 0
    for c in admission_criteria.get_all_scoring_score_criteria():
        main_total += total_weight_scale * c.value
    
    for c in admission_criteria.get_all_scoring_score_criteria():
        # print(total_weight_scale)
        # print("div:", c.child_total_values, c)
        this_weight_scale = total_weight_scale // c.child_total_values
        if c.has_children():
            if c.relation == 'SUM':
                total = sum([child.value for child in c.childs.all()])
                for child in c.childs.all():
                    score_criterias.append((
                        (int(child.value) * int(c.value) * this_weight_scale,
                         main_total),
                        (c.value, child.value, total),
                        child))
            elif c.relation == 'MAX':
                score_criterias.append((
                    (int(c.value) * this_weight_scale, main_total),
                    (c.value,1,1),
                    ['MAX'] + [child for child in c.childs.all()]))

            else:
                print_error('Error type:', c.relation)
                for child in c.childs.all():
                    print_error(f"    - {child}")
                is_error = True
        else:
            score_criterias.append(((int(c.value) * this_weight_scale, main_total),
                                    (c.value,1,1),
                                    c))

    for c in score_criterias:
        if type(c[2]) != list:
            fix_score_type(c[2], curriculum_major)
        else:
            for cc in c[2][1:]:
                fix_score_type(cc, curriculum_major)


    print_scoring = False

    results = []
    for s in score_criterias:
        percent = s[0][0]
        if percent == 0:
            continue

        if type(s[2]) != list:
            if print_scoring:
                print_error("%.2f" % percent,
                      s[2].score_type,
                      s)
            if s[2].score_type != 'OTHER':
                results.append((s[2].score_type, int(percent)))
            else:
                results.append((s[2].description, int(percent)))
        else:
            if print_scoring:
                print_error("%.2f" % percent,
                      s[2][0],
                      [sss.score_type for sss in s[2][1:]],
                      s)
            results.append(('MAX(' + ','.join([sss.score_type for sss in s[2][1:]]) + ')', int(percent)))

    if is_error:
        print_error('=============', curriculum_major.faculty, '==========', curriculum_major.cupt_code)

    return results

def export_curriculum_major_criterias(admission_project):
    faculties = Faculty.objects.all()
    
    admission_criterias = (AdmissionCriteria
                           .objects
                           .filter(admission_project_id=admission_project.id,
                                   is_deleted=False)
                           .order_by('faculty_id'))

    curriculum_major_results = {}

    for admission_criteria in admission_criterias:
        curriculum_major_criterias = admission_criteria.curriculummajoradmissioncriteria_set.all()

        if len(curriculum_major_criterias) == 0:
            continue
            
        curriculum_major = curriculum_major_criterias[0].curriculum_major

        min_scores_vecs = min_score_vectors(admission_criteria, curriculum_major)
        if len(min_scores_vecs) > 1:
            if min_scores_vecs[0] == min_scores_vecs[1]:
                print_error('ERROR two rows', curriculum_major, len(min_scores_vecs))
                print_error('BUT they are the same... OK!')
            else:
                print_error('**** ERROR two rows', curriculum_major, len(min_scores_vecs))
                print_error(min_scores_vecs[0])
                print_error(min_scores_vecs[1])
            
        min_scores = min_scores_vecs[0]

        non_zero_min_scores = { k:min_scores[k] for k in min_scores if min_scores[k] > 0 }

        if admission_criteria.additional_condition != '':
            non_zero_min_scores['additional_condition'] = admission_criteria.additional_condition
            print_error(" > ", curriculum_major, "---->", admission_criteria.additional_condition)

        scoring_scores = score_vector_from_criterias(admission_criteria, curriculum_major)

        for mc in curriculum_major_criterias:
            curriculum_major = mc.curriculum_major
            major_cupt_code = curriculum_major.cupt_code

            row = {
                'criteria_key': f'{major_cupt_code.program_code}-{major_cupt_code.major_code}-{mc.id}',
                'required_score_criteria': non_zero_min_scores,
                'scoring_score_criteria': scoring_scores,
                'faculty': curriculum_major.faculty.title,
                'title': major_cupt_code.display_title(),
                'slot':  mc.slots,
                'faculty_id': curriculum_major.faculty.id,
                'program_type_code':major_cupt_code.program_type_code,
                'program_code':major_cupt_code.program_code,
                'major_code':major_cupt_code.major_code,
            }

            if major_cupt_code.get_program_major_code() in curriculum_major_results:
                print_error('>>>>>>>>>  ERROR too many criterias for', major_cupt_code, major_cupt_code.get_program_major_code())

            if major_cupt_code.get_program_major_code() not in curriculum_major_results:
                curriculum_major_results[major_cupt_code.get_program_major_code()] = []

            curriculum_major_results[major_cupt_code.get_program_major_code()].append(row)

    return curriculum_major_results

def get_program_major_code_from_major(major):
    items = major.get_detail_items()
    return tuple(items[-2:])

def main():
    project_id = sys.argv[1]

    dump_without_majors = False
    if len(sys.argv) > 2:
        dump_without_majors = sys.argv[2] == '--dump-all'
    
    project_ids = [project_id]

    all_rows = []
    
    for project_id in project_ids:
        admission_project = AdmissionProject.objects.get(pk=project_id)

        exported_curriculum_major_criterias = export_curriculum_major_criterias(admission_project)

        project_rows = []

        if dump_without_majors:
            for k in exported_curriculum_major_criterias:
                for r in exported_curriculum_major_criterias[k]:
                    all_rows.append(r)

            continue
            
        for major in admission_project.major_set.all():
            program_major_code = get_program_major_code_from_major(major)
            if program_major_code in exported_curriculum_major_criterias:
                res_list = copy.deepcopy(exported_curriculum_major_criterias[program_major_code])
                if len(res_list) == 1:
                    res = res_list[0]
                    #print(res)
                else:
                    print_error('==========ERROR=========')
                    print_error(res_list)
                    res = res_list[0]
                res['major_number'] = major.number
                res['admission_project_id'] = admission_project.id
                res['admission_project'] = admission_project.title
                project_rows.append(res)

        all_rows += project_rows

    print(json.dumps(all_rows, indent=1))

if __name__ == '__main__':
    main()
