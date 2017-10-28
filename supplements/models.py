import json

from django.db import models

from regis.models import Applicant
from appl.models import School, AdmissionProject

class TopSchool(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE)


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
                                     related_name='results')
    subject_id = models.CharField(max_length=10)
    section_id = models.IntegerField()
    grade = models.CharField(max_length=5)

    def get_course_title_display(self):
        if self.subject_id in AdvancedPlacementResult.SUBJECT_TITLE:
            return AdvancedPlacementResult.SUBJECT_TITLE[self.subject_id]
        else:
            return ''

class ProjectSupplement(models.Model):
    applicant = models.ForeignKey(Applicant)
    admission_project = models.ForeignKey(AdmissionProject)
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
    if admission_project.title in PROJECT_SUPPLEMENTS:
        supplement_configs = PROJECT_SUPPLEMENTS[admission_project.title]
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
}


PROJECT_ADDITIONAL_BLOCKS = {
    'เรียนล่วงหน้า': [
        ProjectBlockConfig('ap_course_results',
                           'ผลการเรียนจากโครงการเรียนล่วงหน้า',
                           'supplements/ap/course_results.html',
                           'supplements.views.blocks.load_ap_course_results'),
    ],
}
