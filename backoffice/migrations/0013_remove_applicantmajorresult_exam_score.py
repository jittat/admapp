# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-05-23 12:57
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0012_applicantmajorresult_project_application'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='applicantmajorresult',
            name='exam_score',
        ),
    ]