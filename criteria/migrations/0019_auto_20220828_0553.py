# Generated by Django 3.2.15 on 2022-08-28 05:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criteria', '0018_alter_admissioncriteria_additional_interview_condition'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissioncriteria',
            name='accepted_student_curriculum_type_flags',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='curriculummajoradmissioncriteria',
            name='add_limit',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]