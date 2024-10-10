from django.db import models

import json

from appl.models import AdmissionProject
from django.core.exceptions import ValidationError

class CuptExportConfig(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    config_json = models.TextField(blank=True)

    def __str__(self):
        return self.admission_project.title

    def clean(self):
        try:
            json.loads(self.config_json)
        except:
            raise ValidationError('Incorrect JSON config')


class CuptExportLog(models.Model):
    output_filename = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.output_filename


class CuptExportCustomProject(models.Model):
    cupt_code = models.CharField(max_length=10)
    title = models.CharField(max_length=400)

    def __str__(self):
        return f'{self.cupt_code} - {self.title}'

class CuptExportAdditionalProjectRule(models.Model):
    program_major_code = models.CharField(max_length=30)
    custom_project = models.ForeignKey('CuptExportCustomProject',
                                       on_delete=models.CASCADE)
    rule_json = models.TextField(blank=True)

    def __str__(self):
        return f'{self.program_major_code} - {self.custom_project.cupt_code}'

