# Generated by Django 4.1.13 on 2024-08-30 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0084_admissionproject_custom_interview_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissionproject',
            name='display_rank',
            field=models.IntegerField(default=0, verbose_name='สำหรับใช้เรียงรายการ'),
        ),
    ]
