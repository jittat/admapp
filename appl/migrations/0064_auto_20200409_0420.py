# Generated by Django 2.2.10 on 2020-04-09 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0063_auto_20200409_0349'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectuploadeddocument',
            name='is_common_document',
            field=models.BooleanField(default=False, verbose_name='ใช้ทุกโครงการ'),
        ),
        migrations.AddField(
            model_name='projectuploadeddocument',
            name='is_interview_document',
            field=models.BooleanField(default=False, verbose_name='ใช้สำหรับสัมภาษณ์'),
        ),
    ]