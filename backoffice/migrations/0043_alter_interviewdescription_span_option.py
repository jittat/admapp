# Generated by Django 4.1.1 on 2023-04-11 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0042_interviewdescription_span_option_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='interviewdescription',
            name='span_option',
            field=models.IntegerField(choices=[(0, 'ไม่มีการเชื่อมโยงไปยังสาขาหรือโครงการอื่น'), (1, 'เชื่อมโยงทุกสาขาในโครงการนี้'), (2, 'เชื่อมโยงทุกโครงการของสาขานี้'), (3, 'เชื่อมโยงแยกโครงการ-สาขา')], default=0, verbose_name='การเชื่อมโยงรายละเอียดการสัมภาษณ์'),
        ),
    ]
