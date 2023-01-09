# Generated by Django 4.1.1 on 2022-10-13 05:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criteria', '0021_cuptexportconfig'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImportedCriteriaJSON',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('program_id', models.CharField(max_length=20)),
                ('major_id', models.CharField(blank=True, max_length=5)),
                ('project_id', models.CharField(max_length=10)),
                ('criteria_type', models.CharField(max_length=30)),
                ('data_json', models.TextField()),
            ],
        ),
    ]