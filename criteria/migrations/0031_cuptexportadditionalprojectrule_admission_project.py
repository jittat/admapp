# Generated by Django 4.1.13 on 2024-10-11 02:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0085_admissionproject_display_rank'),
        ('criteria', '0030_alter_cuptexportadditionalprojectrule_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='cuptexportadditionalprojectrule',
            name='admission_project',
            field=models.ForeignKey(default=28, on_delete=django.db.models.deletion.CASCADE, to='appl.admissionproject'),
            preserve_default=False,
        ),
    ]
