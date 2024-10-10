# Generated by Django 4.1.13 on 2024-10-10 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('criteria', '0028_admissioncriteria_custom_interview_date_str'),
    ]

    operations = [
        migrations.CreateModel(
            name='CuptExportCustomProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cupt_code', models.CharField(max_length=10)),
                ('title', models.CharField(max_length=400)),
            ],
        ),
        migrations.CreateModel(
            name='CuptExportAdditionalProjectRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program_major_code', models.CharField(max_length=30)),
                ('rule_json', models.TextField(blank=True)),
                ('custom_project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='criteria.cuptexportcustomproject')),
            ],
        ),
    ]
