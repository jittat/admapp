# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-11-13 18:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0007_judgecomment_is_super'),
    ]

    operations = [
        migrations.AddField(
            model_name='judgecomment',
            name='major',
            field=models.IntegerField(default=0),
        ),
    ]