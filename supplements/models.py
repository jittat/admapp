import json

from django.db import models

from regis.models import Applicant
from appl.models import School, AdmissionProject

class TopSchool(models.Model):
    school = models.OneToOneField(School,
                                  on_delete=models.CASCADE)


class AdvancedPlacementApplicant(models.Model):
    national_id = models.CharField(max_length=16,
                                   unique=True)
    student_id = models.CharField(max_length=12,
                                  unique=True)


class AdvancedPlacementResult(models.Model):
    SUBJECT_TITLE = {
        '01403000': 'เคมี',
        '01417000': 'คณิตศาสตร์',
        '01420000': 'ฟิสิกส์',
        '01424000': 'ชีววิทยา',
    }
    
    ap_applicant = models.ForeignKey(AdvancedPlacementApplicant,
                                     related_name='results',
                                     on_delete=models.CASCADE)
    subject_id = models.CharField(max_length=10)
    section_id = models.IntegerField()
    grade = models.CharField(max_length=5)

    def get_course_title_display(self):
        if self.subject_id in AdvancedPlacementResult.SUBJECT_TITLE:
            return AdvancedPlacementResult.SUBJECT_TITLE[self.subject_id]
        else:
            return ''

class ProjectSupplement(models.Model):
    applicant = models.ForeignKey(Applicant,
                                  on_delete=models.CASCADE)
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    json_data = models.TextField(blank=True)

    def __str__(self):
        if self.applicant:
            return '%s (%s)' % (self.name, str(self.applicant))
        else:
            return None

    def get_data(self):
        if self.json_data == '':
            return {}
        else:
            try:
                return self.data
            except:
                self.data = json.loads(self.json_data)
                return self.data

    def set_data(self, data):
        self.data = data
        self.json_data = json.dumps(data)


    @staticmethod
    def get_applicant_supplements_as_dict(applicant):
        all_supplements = ProjectSupplement.objects.filter(applicant=applicant)
        results = {}
        for s in all_supplements:
            results[s.name] = s
        return results
        

class ProjectSupplementConfig(object):
    def __init__(self,
                 name,
                 title,
                 is_required,
                 template_name,
                 form_prefix,
                 form_init_function,
                 form_processing_function,
                 backoffice_template):
        
        self.name = name
        self.title = title
        self.is_required = is_required
        self.template_name = template_name
        self.form_prefix = form_prefix
        self.form_init_function = form_init_function
        self.form_processing_function = form_processing_function
        self.backoffice_template = backoffice_template


def load_project_supplements(applicant, admission_project, configs):
    all_supplements = ProjectSupplement.objects.filter(applicant=applicant,
                                                       admission_project=admission_project).all()
    m = {}
    for s in all_supplements:
        m[s.name] = s
        
    supplements = {}
    for config in configs:
        if config.name in m:
            supplements[config.name] = m[config.name]
        else:
            supplements[config.name] = None
    return supplements


def load_supplement_configs_with_instance(applicant, admission_project):
    from supplements.models import PROJECT_SUPPLEMENTS, ProjectSupplement

    all_supplements = ProjectSupplement.get_applicant_supplements_as_dict(applicant)
    
    supplement_configs = []
    if admission_project.short_title in PROJECT_SUPPLEMENTS:
        supplement_configs = PROJECT_SUPPLEMENTS[admission_project.short_title]
        for c in supplement_configs:
            if c.name in all_supplements:
                c.supplement_instance = all_supplements[c.name]
            else:
                c.supplement_instance = None

    return supplement_configs


class ProjectBlockConfig(object):
    def __init__(self,
                 name,
                 title,
                 template_name,
                 context_init_function):
        
        self.name = name
        self.title = title
        self.template_name = template_name
        self.context_init_function = context_init_function

def is_tcas5_gpa_form_required(applicant,
                               admission_project,
                               supplement_config):
    from appl.models import AdmissionRound
    admission_round = AdmissionRound.objects.get(pk=6)
    active_application = applicant.get_active_application(admission_round)
    if not active_application:
        return False

    major_selection = active_application.get_major_selection()
    if major_selection and major_selection.major_list == '10':
        return True
    
    return False
    
PROJECT_SUPPLEMENTS = {
    'นักกีฬาทีมชาติและเยาวชนทีมชาติ': [
        ProjectSupplementConfig('sport_type',
                                'ประเภทกีฬาและระดับ',
                                True,
                                'supplements/nat_sport/sport_type.html',
                                'sport_type_',
                                'supplements.views.forms.nat_sport.init_sport_type_form',
                                'supplements.views.forms.nat_sport.process_sport_type_form',
                                'supplements/backoffice/nat_sport/sport_type.html'),
        ProjectSupplementConfig('sport_history',
                                'ผลการแข่งขัน',
                                True,
                                'supplements/nat_sport/sport_history.html',
                                'sport_history_',
                                'supplements.views.forms.nat_sport.init_sport_history_form',
                                'supplements.views.forms.nat_sport.process_sport_history_form',
                                'supplements/backoffice/nat_sport/sport_history.html'),
    ],
    'โควตานักกีฬาดีเด่นฯ': [
        ProjectSupplementConfig('gen_sport_type',
                                'ประเภทกีฬาและระดับ',
                                True,
                                'supplements/gen_sport/sport_type.html',
                                'gen_sport_type_',
                                'supplements.views.forms.gen_sport.init_sport_type_form',
                                'supplements.views.forms.gen_sport.process_sport_type_form',
                                'supplements/backoffice/gen_sport/sport_type.html'),
        ProjectSupplementConfig('gen_sport_history',
                                'ผลการแข่งขัน',
                                True,
                                'supplements/gen_sport/sport_history.html',
                                'gen_sport_history_',
                                'supplements.views.forms.gen_sport.init_sport_history_form',
                                'supplements.views.forms.gen_sport.process_sport_history_form',
                                'supplements/backoffice/gen_sport/sport_history.html'),
    ],
    'โควตาศิลปวัฒนธรรมฯ': [
        ProjectSupplementConfig('cultural_type',
                                'ประเภทศิลปวัฒนธรรม',
                                True,
                                'supplements/cultural/cultural_type.html',
                                'cultural_type_',
                                'supplements.views.forms.cultural.init_cultural_type_form',
                                'supplements.views.forms.cultural.process_cultural_type_form',
                                'supplements/backoffice/cultural/cultural_type.html'),
        ProjectSupplementConfig('cultural_history',
                                'ประวัติการแข่งขัน/การแสดง',
                                True,
                                'supplements/cultural/cultural_history.html',
                                'cultural_history_',
                                'supplements.views.forms.cultural.init_cultural_history_form',
                                'supplements.views.forms.cultural.process_cultural_history_form',
                                'supplements/backoffice/cultural/cultural_history.html'),
        ProjectSupplementConfig('cultural_exam',
                                'การสมัครทดสอบความสามารถ',
                                True,
                                'supplements/cultural/cultural_exam.html',
                                'cultural_exam_',
                                'supplements.views.forms.cultural.init_cultural_exam_form',
                                'supplements.views.forms.cultural.process_cultural_exam_form',
                                'supplements/backoffice/cultural/cultural_exam.html'),
    ],
    'รับตรงอิสระ': [
        ProjectSupplementConfig('tcas5_fisheries',
                                'ผลการเรียนเฉลี่ยแยกกลุ่มสาระ (สำหรับกรณีที่สมัครคณะประมง)',
                                is_tcas5_gpa_form_required,
                                'supplements/tcas5/gpa_form.html',
                                'tcas5_gpa_',
                                'supplements.views.forms.tcas5.init_gpa_form',
                                'supplements.views.forms.tcas5.process_gpa_form',
                                'supplements/backoffice/tcas5/gpa.html'),
    ],
}


PROJECT_ADDITIONAL_BLOCKS = {
    'เรียนล่วงหน้า': [
        ProjectBlockConfig('ap_course_results',
                           'ผลการเรียนจากโครงการเรียนล่วงหน้า',
                           'supplements/ap/course_results.html',
                           'supplements.views.blocks.load_ap_course_results'),
    ],
    'รับตรงอิสระ': [
        ProjectBlockConfig('tcas5_block',
                           'ข้อมูลเพิ่มเติมสำหรับการสมัคร',
                           'supplements/tcas5/info.html',
                           'supplements.views.blocks.load_tcas5_block'),
    ],
}

ap_course_results = None

def load_applicant_ap_results(applicant,
                              admission_project,
                              admission_round):
    global ap_course_results

    if not ap_course_results:
        SUBJECT_IDX = {
            '01403000': 0,
            '01417000': 1,
            '01420000': 2,
            '01424000': 3,
        }
        
        ap_course_results = {}
        ap_applicants = dict([(a.id, a) for a
                              in AdvancedPlacementApplicant.objects.all()])
        for res in AdvancedPlacementResult.objects.all():
            national_id = ap_applicants[res.ap_applicant_id].national_id
            if national_id not in ap_course_results:
                ap_app = ap_applicants[res.ap_applicant_id]
                ap_app.course_results = ['-','-','-','-']
                ap_course_results[ap_app.national_id] = ap_app

            ap_app = ap_course_results[national_id]
            ap_app.course_results[SUBJECT_IDX[res.subject_id]] = res.grade

        

    if applicant.national_id in ap_course_results:
        return ap_course_results[applicant.national_id]
    else:
        return None

PROJECT_APPLICANT_LIST_ADDITIONS = {
    'เรียนล่วงหน้า': {
        'loader': load_applicant_ap_results,
        'col_count': 4,
        'header_template': 'supplements/ap/applicant_info_head.html',
        'template': 'supplements/ap/applicant_info.html',
    },
}
