# Generated by Django 3.2.7 on 2021-10-02 17:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criteria', '0016_auto_20201029_0339'),
    ]

    operations = [
        migrations.AddField(
            model_name='admissioncriteria',
            name='additional_interview_condition',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]