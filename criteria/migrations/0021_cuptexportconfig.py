# Generated by Django 4.1.1 on 2022-09-29 08:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0079_admissionproject_is_cupt_export_only_major_list'),
        ('criteria', '0020_alter_admissioncriteria_accepted_student_curriculum_type_flags'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuptExportConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config_json', models.TextField(blank=True)),
                ('admission_project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appl.admissionproject')),
            ],
        ),
    ]
