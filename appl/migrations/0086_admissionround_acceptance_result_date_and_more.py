# Generated by Django 4.1.13 on 2024-11-16 06:59

import datetime
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0085_admissionproject_display_rank'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissionround',
            name='acceptance_result_date',
            field=models.DateField(default=datetime.date(2024, 11, 16), verbose_name='วันที่ประกาศผลการคัดเลือก (สำหรับแจ้งในข้อความ)'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='admissionround',
            name='clearing_house_dates_short',
            field=models.CharField(blank=True, max_length=50, verbose_name='วันที่ยืนยันสิทธิ์ในระบบทปอ.แบบสั้น (สำหรับแจ้งในข้อความ)'),
        ),
        migrations.AlterField(
            model_name='admissionround',
            name='clearing_house_dates',
            field=models.CharField(blank=True, max_length=50, verbose_name='วันที่ยืนยันสิทธิ์ในระบบทปอ. (สำหรับแจ้งในข้อความ)'),
        ),
        migrations.AlterField(
            model_name='educationalprofile',
            name='gpa',
            field=models.FloatField(default=0, help_text='ในกรณีที่กำลังศึกษาชั้นม.6 ให้กรอกเกรดเฉลี่ย 5 ภาคการศึกษา แต่ถ้าคะแนนภาคต้นยังไม่เรียบร้อย สามารถกรอกแค่ 4 ภาคการศึกษาได้ ถ้าจบการศึกษาแล้วให้กรอกเกรดเฉลี่ย 6 ภาคการศึกษา', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(5.0)], verbose_name='GPAX'),
        ),
    ]
