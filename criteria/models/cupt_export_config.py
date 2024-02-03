from django.db import models

from appl.models import AdmissionProject


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
