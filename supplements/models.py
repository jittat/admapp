from django.db import models

from appl.models import School

class TopSchool(models.Model):
	 school = models.OneToOneField(School, on_delete=models.CASCADE)

