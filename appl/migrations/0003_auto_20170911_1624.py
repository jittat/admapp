# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-11 16:24
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0002_projectuploadeddocument_uploadeddocument'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadeddocument',
            name='project_uploaded_document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='uploaded_document_set', to='appl.ProjectUploadedDocument'),
        ),
    ]
