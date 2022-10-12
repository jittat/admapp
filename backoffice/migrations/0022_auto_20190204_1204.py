# Generated by Django 2.1.3 on 2019-02-04 12:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0021_adjustmentmajorslot'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='adjustmentmajorslot',
            options={'ordering': ['major_full_code']},
        ),
        migrations.AddField(
            model_name='adjustmentmajorslot',
            name='cupt_code',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AlterField(
            model_name='adjustmentmajorslot',
            name='adjustment_major',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slots', to='backoffice.AdjustmentMajor'),
        ),
    ]
