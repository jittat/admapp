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

class ProjectSupplementConfig(object):
    def __init__(self,
                 name,
                 title,
                 template_name,
                 form_prefix,
                 form_processing_function):
        
        self.name = name
        self.title = title
        self.template_name = template_name
        self.form_prefix = form_prefix
        self.form_processing_function = form_processing_function


PROJECT_SUPPLEMENTS = {
    'นักกีฬาทีมชาติและเยาวชนทีมชาติ': [
        ProjectSupplementConfig('sport_type',
                                'ประเภทกีฬา',
                                'supplements/nat_sport/sport_type.html',
                                'sport_type_',
                                'supplements.views.forms.nat_sport.process_sport_type'),
    ],
}
    
