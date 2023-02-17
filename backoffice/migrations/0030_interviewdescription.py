# Generated by Django 4.1.1 on 2023-02-17 11:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0080_alter_educationalprofile_sci_credit'),
        ('backoffice', '0029_auto_20210505_1207'),
    ]

    operations = [
        migrations.CreateModel(
            name='InterviewDescription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interview_options', models.IntegerField(choices=[(0, 'ไม่มีการสัมภาษณ์'), (1, 'สัมภาษณ์ออนไลน์'), (2, 'สัมภาษณ์ที่สถานที่')], verbose_name='ทางเลือกการสัมภาษณ์')),
                ('preparation_descriptions', models.TextField(blank=True, verbose_name='รายละเอียดการเตรียมตัว')),
                ('preparation_image', models.FileField(blank=True, upload_to='interview_docs', verbose_name='รูปประกอบการเตรียมตัว')),
                ('descriptions', models.TextField(blank=True, verbose_name='รายละเอียดการสัมภาษณ์')),
                ('description_image', models.FileField(blank=True, upload_to='interview_docs', verbose_name='รูปประกอบการเตรียมตัว')),
                ('contacts', models.JSONField(blank=True, verbose_name='ข้อมูลการติดต่อ')),
                ('admission_project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='appl.admissionproject')),
                ('admission_round', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appl.admissionround')),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appl.faculty')),
                ('major', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='appl.major')),
            ],
        ),
    ]
