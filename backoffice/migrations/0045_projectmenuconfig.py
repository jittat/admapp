# Generated by Django 4.1.1 on 2024-02-03 05:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0082_admissionproject_is_custom_graduate_year_allowed'),
        ('backoffice', '0044_alter_interviewdescription_span_option_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectMenuConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('menu_flag_json', models.TextField()),
                ('admission_project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='appl.admissionproject')),
                ('admission_round', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='appl.admissionround')),
            ],
        ),
    ]
