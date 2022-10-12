# Generated by Django 2.1.3 on 2018-11-19 23:56

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0058_admissionresult_is_interview_absent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admissionproject',
            name='campus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='appl.Campus'),
        ),
        migrations.AlterField(
            model_name='educationalprofile',
            name='gpa',
            field=models.FloatField(default=0, help_text='สำหรับการคัดเลือก TCAS รอบ 5 ให้กรอกเกรดเฉลี่ย 6 ภาคการศึกษา', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(5.0)], verbose_name='GPAX'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='applicant',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='regis.Applicant'),
        ),
    ]
