# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-05-24 13:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0015_auto_20180524_0551'),
    ]

    operations = [
        migrations.AddField(
            model_name='applicantmajorresult',
            name='other_major_numbers',
            field=models.CharField(blank='', default='', max_length=30),
        ),
    ]
