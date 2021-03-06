# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-02 22:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0040_admissionprojectround_accepted_for_interview_result_frozen'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissionproject',
            name='cupt_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='faculty',
            name='cupt_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='faculty',
            name='ku_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='major',
            name='cupt_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='major',
            name='cupt_study_type_code',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='major',
            name='ku_code',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
