from django.db import models

from criteria.models.admission_criteria import AdmissionCriteria
from criteria.models.curriculum_major import CurriculumMajor


class CurriculumMajorAdmissionCriteria(models.Model):
    """
    This is the join table.
    """
    curriculum_major = models.ForeignKey(
        CurriculumMajor, on_delete=models.CASCADE)
    admission_criteria = models.ForeignKey(
        AdmissionCriteria, on_delete=models.CASCADE)

    slots = models.IntegerField()
    add_limit = models.CharField(max_length=10, blank=True)

    DEFAULT_ADD_LIMIT = 'A'

    version = models.IntegerField(default=1)

    def add_limit_display(self):
        if self.add_limit == '':
            return CurriculumMajorAdmissionCriteria.DEFAULT_ADD_LIMIT
        else:
            return self.add_limit

    def add_limit_type_display(self):
        if self.add_limit == '':
            return CurriculumMajorAdmissionCriteria.DEFAULT_ADD_LIMIT
        else:
            return self.add_limit[0]

    def add_limit_num(self):
        if self.add_limit.startswith('C'):
             return int(self.add_limit[1:])
        else:
            return 0
