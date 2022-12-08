from django.db import models


class ImportedCriteriaJSON(models.Model):
    program_id = models.CharField(max_length=20)
    major_id = models.CharField(max_length=5,blank=True)
    project_id = models.CharField(max_length=10)

    criteria_type = models.CharField(max_length=30)

    data_json = models.TextField()

    def __str__(self):
        if self.major_id == '':
            return f'{self.project_id} {self.program_id}'
        else:
            return f'{self.project_id} {self.program_id}0{self.major_id}'
