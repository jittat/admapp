from django.db import models

from appl.models import AdmissionProject, Faculty, Major

COMPONENT_WEIGHT_TYPE_CHOICES = []


class CurriculumMajor(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    cupt_code = models.ForeignKey('MajorCuptCode',
                                  on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    major = models.ForeignKey(Major,
                              on_delete=models.CASCADE, null=True)
    admission_criterias = models.ManyToManyField(
        'AdmissionCriteria', through='CurriculumMajorAdmissionCriteria')

    def is_with_some_admission_criteria(self):
        return self.admission_criterias.filter(is_deleted=False).count() != 0

    class Meta:
        ordering = ['cupt_code']

    def get_component_weight_type_choices(self):
        component_weight_type = self.cupt_code.component_weight_type

        if component_weight_type.endswith('0'):
            prefix = 'CW' + component_weight_type[0]
        else:
            prefix = 'CW' + component_weight_type

        choices = [ch for ch in COMPONENT_WEIGHT_TYPE_CHOICES
                   if ch[0].startswith(prefix)]
        return choices

    @staticmethod
    def get_component_weight_type_choices_unique(curriculum_majors):
        added = set()
        choices = []
        for m in curriculum_majors:
            for ch in m.get_component_weight_type_choices():
                if ch[0] not in added:
                    choices.append(ch)
                    added.add(ch[0])
        return choices
