# Generated by Django 4.1.7 on 2023-03-26 17:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0080_alter_educationalprofile_sci_credit'),
        ('criteria', '0022_importedcriteriajson'),
        ('backoffice', '0033_alter_addmissionprojectmajorcuptcodeinterviewdescription_admission_project'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AddmissionProjectMajorCuptCodeInterviewDescription',
            new_name='AdmissionProjectMajorCuptCodeInterviewDescription',
        ),
    ]
