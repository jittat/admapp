# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.forms import ModelForm


# Create your models here.
class Province(models.Model):
    province = models.CharField(max_length=30)

    def __str__(self):
    	return "%s" % (self.province)


class School(models.Model):
	school_name = models.CharField(max_length=80)

	def __str__(self):
		return "%s" % (self.school_name)
