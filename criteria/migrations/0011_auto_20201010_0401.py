# Generated by Django 2.2.13 on 2020-10-10 04:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('criteria', '0010_admissioncriteria_created_at'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='curriculummajor',
            options={'ordering': ['cupt_code']},
        ),
        migrations.RemoveField(
            model_name='majorcuptcode',
            name='major',
        ),
    ]