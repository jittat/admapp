# Generated by Django 4.1.7 on 2023-03-26 17:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0080_alter_educationalprofile_sci_credit'),
        ('backoffice', '0032_remove_interviewdescription_major_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addmissionprojectmajorcuptcodeinterviewdescription',
            name='admission_project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appl.admissionproject'),
        ),
    ]
