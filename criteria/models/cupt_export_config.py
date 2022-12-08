from django.db import models

from appl.models import AdmissionProject


class CuptExportConfig(models.Model):
    admission_project = models.ForeignKey(AdmissionProject,
                                          on_delete=models.CASCADE)
    config_json = models.TextField(blank=True)

    def __str__(self):
        return self.admission_project.title
