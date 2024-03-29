# Generated by Django 3.2.15 on 2022-08-28 05:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0077_auto_20211222_0321'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissionproject',
            name='is_custom_add_limit_criteria',
            field=models.BooleanField(default=False, verbose_name='ให้ระบุจำนวนรับเพิ่มในกรณีที่ผู้สมัครเกินและมีคะแนนเท่ากัน'),
        ),
        migrations.AddField(
            model_name='admissionproject',
            name='is_custom_curriculum_type_allowed',
            field=models.BooleanField(default=False, verbose_name='อนุญาตให้แก้ไขประเภทหลักสูตรโรงเรียนได้'),
        ),
    ]
