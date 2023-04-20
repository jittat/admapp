# Generated by Django 4.1.1 on 2023-04-21 01:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0044_alter_interviewdescription_span_option_and_more'),
        ('appl', '0080_alter_educationalprofile_sci_credit'),
    ]

    operations = [
        migrations.CreateModel(
            name='MajorInterviewDescriptionCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interview_description', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backoffice.interviewdescription')),
                ('major', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='appl.major')),
            ],
        ),
    ]
