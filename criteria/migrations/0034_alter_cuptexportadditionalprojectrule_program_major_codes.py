# Generated by Django 4.1.13 on 2024-10-11 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criteria', '0033_alter_cuptexportadditionalprojectrule_program_major_codes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuptexportadditionalprojectrule',
            name='program_major_codes',
            field=models.CharField(max_length=200),
        ),
    ]