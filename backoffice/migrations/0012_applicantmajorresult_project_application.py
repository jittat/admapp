# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-05-23 12:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0055_auto_20180523_0259'),
        ('backoffice', '0011_auto_20180523_1008'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicantmajorresult',
            name='project_application',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='appl.ProjectApplication'),
        ),
    ]