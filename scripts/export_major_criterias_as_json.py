from django_bootstrap import bootstrap
bootstrap()

import sys
import json
import copy

import yaml
    
from appl.models import AdmissionProject, Faculty
from criteria.models import AdmissionCriteria

error_report_file = sys.stderr

SCORE_TYPE_TAG_FILENAME = 'score_type_tags.yaml'

FIELDS = [
    'min_gpax5',
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
    'min_gpa22_23',
    'min_tgat',
    'min_tgat1',
    'min_tgat2',
    'min_tgat3',
    'min_tpat1',
    'min_tpat11',
    'min_tpat12',
    'min_tpat13',
    'min_tpat2',
    'min_tpat21',
    'min_tpat22',
    'min_tpat23',
    'min_tpat3',
    'min_tpat4',
    'min_tpat5',
    'min_a_lv_61',
    'min_a_lv_62',
    'min_a_lv_63',
    'min_a_lv_64',
    'min_a_lv_65',
    'min_a_lv_66',
    'min_a_lv_70',
    'min_a_lv_81',
    'min_a_lv_82',
    'min_a_lv_83',
    'min_a_lv_84',
    'min_a_lv_85',
    'min_a_lv_86',
    'min_a_lv_87',
    'min_a_lv_88',
    'min_a_lv_89',
    'min_vnet_51',
    'min_vnet_511',
    'min_vnet_512',
    'min_vnet_513',
    'min_vnet_514',
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
    'min_swu_set',
    'min_det',
    'min_mu_elt',
    'min_sat',
    'min_cefr',
]

COMPONENT_WEIGHT_OPTIONS = []

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
    "GPAX_5_SEMESTER": 'min_gpax5',
    "GPAX": "min_gpax",
    "UNIT_MATH": 'min_credit_gpa22',
    "UNIT_FOREIGN": 'min_credit_gpa28',
    "UNIT_SCI": 'min_credit_gpa23',

    "MIN_GPA21": 'min_gpa21',
    "MIN_GPA22": 'min_gpa22',
    "MIN_GPA23": 'min_gpa23',
    "MIN_GPA28": 'min_gpa28',
    "TGAT": 'min_tgat',
    "TGAT1": 'min_tgat1',
    "TGAT2": 'min_tgat2',
    "TGAT3": 'min_tgat3',
    "TPAT1": 'min_tpat1',
    "TPAT2": 'min_tpat2',
    "TPAT21": 'min_tpat21',
    "TPAT22": 'min_tpat22',
    "TPAT23": 'min_tpat23',
    "TPAT3": 'min_tpat3',
    "TPAT4": 'min_tpat4',
    "TPAT5": 'min_tpat5',
    "A61Math1": 'min_a_lv_61',
    "A62Math2": 'min_a_lv_62',
    "A63Sci": 'min_a_lv_63',
    "A64Phy": 'min_a_lv_64',
    "A65Chem": 'min_a_lv_65',
    "A66Bio": 'min_a_lv_66',
    "A70Soc": 'min_a_lv_70',
    "A81Thai": 'min_a_lv_81',
    "A82Eng": 'min_a_lv_82',
    "A83Fre": 'min_a_lv_83',
    "A84Ger": 'min_a_lv_84',
    "A85Jap": 'min_a_lv_85',
    "A86Kor": 'min_a_lv_86',
    "A87Chi": 'min_a_lv_87',
    "A88Bal": 'min_a_lv_88',
    "A89Spn": 'min_a_lv_89',
    "VNET": 'min_vnet_51',
    "TOEFL_IBT": 'min_toefl_ibt',
    "TOEFL_PBT_ITP": 'min_toefl_pbt',
    "TOEFL_CBT": 'min_toefl_cbt',
    "TOEFL_PBT_ITP": 'min_toefl_ipt',
    "IELTS": 'min_ielts',
    "TOEIC": 'min_toeic',
    "CU_TEP": 'min_cutep',
    "TU_GET": 'min_tuget',
    "KKU_KEPT": 'min_kept',
    "PSU_TEP": 'min_psutep',
    "KU_EPT": 'min_kuept',
    "CMU_ETEGS": 'min_cmuetegs',
    "SWU_SET": 'min_swu_set',
    "DET": 'min_det',
    "MU_ELT": 'min_mu_elt',

    "TS_TGAT1": 'min_tgat1_tscore',
    "TS_TPAT3": 'min_tpat3_tscore',
    "TS_A61Math1": 'min_a_lv_61_tscore',
    "TS_A64Phy": 'min_a_lv_64_tscore',
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
        if isinstance(c,list):
            this_criterias = min_score_vector_from_criterias(c[1:], curriculum_major)
            this_non_zero_criterias = { k:this_criterias[k] for k in this_criterias if this_criterias[k] > 0 }
            if len(this_non_zero_criterias) == 0:
                continue
            if len(this_non_zero_criterias) == 1:
                k = list(this_non_zero_criterias.keys())[0]
                value_vectors[k] = this_non_zero_criterias[k]
            else:
                value_vectors['OR(' + ','.join([f'{k}={this_criterias[k]}' for k in this_criterias if this_criterias[k] > 0]) + ')'] = 1
            continue
        
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
                    score_criterias.append(
                        ['OR'] + [child for child in c.childs.all()])
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
