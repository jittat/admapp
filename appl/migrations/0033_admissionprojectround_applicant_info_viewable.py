# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-29 15:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0032_auto_20171011_0438'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissionprojectround',
            name='applicant_info_viewable',
            field=models.BooleanField(default=False, verbose_name='สามารถดูรายละเอียดผู้สมัครได้'),
        ),
    ]