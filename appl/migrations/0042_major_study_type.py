# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-03 00:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0041_auto_20171202_2259'),
    ]

    operations = [
        migrations.AddField(
            model_name='major',
            name='study_type',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]