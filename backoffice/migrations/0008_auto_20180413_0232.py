# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-04-13 02:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0054_admissionprojectround_only_bulk_interview_acceptance'),
        ('backoffice', '0007_auto_20171117_1349'),
    ]

    operations = [
        migrations.CreateModel(
            name='MajorInterviewCallDecision',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interview_call_count', models.IntegerField(default=0)),
                ('interview_call_min_score', models.FloatField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField()),
                ('admission_project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appl.AdmissionProject')),
                ('admission_round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appl.AdmissionRound')),
                ('major', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appl.Major')),
            ],
        ),
        migrations.AddIndex(
            model_name='majorinterviewcalldecision',
            index=models.Index(fields=['major', 'admission_round'], name='backoffice__major_i_205235_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='majorinterviewcalldecision',
            unique_together=set([('major', 'admission_round')]),
        ),
    ]