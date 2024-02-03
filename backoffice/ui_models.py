import json

from django.db import models
from django.core.exceptions import ValidationError

from appl.models import AdmissionRound, AdmissionProject

DEFAULT_MENU_FLAGS = {
    'td-interview-result': False,

    # score viewable
    'score-viewable-interview-call-by-scores': False,
    'score-viewable-dropdown-show-applicant': False,

    # score not viewable
    'not-score-viewable-show-applicant': False,

    # interview form
    'interview-form-edit': False,

    # td by itself
    'td-show-scores': False,

    # applicant info
    'td-applicant-info': False,
    'td-applicant-info-dropdown-show-applicant': False,
    'td-applicant-info-dropdown-show-scores': False,

    # download
    'download-dropdown': False,
    'download-gen-info': False,
    'download-scores': False,
    'download-scores-tgat-tpat-label': False,
    'download-score-only-interview': False,
    'download-gen-info-interview': False,
    'download-interview-form': False,
}

class ProjectMenuConfig(models.Model):
    admission_round = models.ForeignKey(AdmissionRound,
                                        blank=True,
                                        null=True,
                                        on_delete=models.CASCADE)
    admission_project = models.ForeignKey(AdmissionProject,
                                          blank=True,
                                          null=True,
                                          on_delete=models.CASCADE)

    menu_flag_json = models.TextField(help_text='Available options are ' +
                                      ','.join(DEFAULT_MENU_FLAGS.keys()))

    def __str__(self):
        if self.admission_round_id != None:
            return str(self.admission_round)
        elif self.admission_project_id != None:
            return str(self.admission_project)
        else:
            return '(empty)'


    def clean(self):
        if (self.admission_round_id == None) and (self.admission_project_id == None):
            raise ValidationError('Both admission round and admission project cannot both be empty.')

        try:
            json.loads(self.menu_flag_json)
        except:
            raise ValidationError('Incorrect JSON config')
            

    @staticmethod
    def load_menu_config_flags(admission_round, admission_project):
        flags = DEFAULT_MENU_FLAGS.copy()

        configs = []
        configs += list(ProjectMenuConfig.objects.filter(admission_round=admission_round))
        configs += list(ProjectMenuConfig.objects.filter(admission_project=admission_project))

        for c in configs:
            cdata = json.loads(c.menu_flag_json)
            for k in cdata:
                if k in flags:
                    flags[k] = cdata[k]
                        
        return flags
