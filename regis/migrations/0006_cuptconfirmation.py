# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-17 01:25
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regis', '0005_applicant_confirmed_application'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuptConfirmation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('national_id', models.CharField(blank=True, max_length=16)),
                ('passport_number', models.CharField(blank=True, max_length=20)),
                ('has_confirmed', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField()),
                ('applicant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cupt_confirmation', to='regis.Applicant')),
            ],
        ),
    ]
