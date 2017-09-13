# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models



# Create your models here.
class Education_form(models.Model):
    school_name = models.CharField(max_length=40)
