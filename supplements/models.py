import json

from django.db import models

from regis.models import Applicant
from appl.models import School, AdmissionProject

class TopSchool(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE)


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
        

class ProjectSupplementConfig(object):
    def __init__(self,
                 name,
                 title,
                 template_name,
                 form_prefix,
                 form_init_function,
                 form_processing_function):
        
        self.name = name
        self.title = title
        self.template_name = template_name
        self.form_prefix = form_prefix
        self.form_init_function = form_init_function
        self.form_processing_function = form_processing_function


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

    
PROJECT_SUPPLEMENTS = {
    'นักกีฬาทีมชาติและเยาวชนทีมชาติ': [
        ProjectSupplementConfig('sport_type',
                                'ประเภทกีฬา',
                                'supplements/nat_sport/sport_type.html',
                                'sport_type_',
                                'supplements.views.forms.nat_sport.init_form',
                                'supplements.views.forms.nat_sport.process_sport_type'),
    ],
}
    
