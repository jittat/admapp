# Generated by Django 2.2.13 on 2020-10-16 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criteria', '0012_majorcuptcode_component_weight_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='scorecriteria',
            options={'ordering': ['primary_order', 'secondary_order']},
        ),
        migrations.AlterField(
            model_name='majorcuptcode',
            name='component_weight_type',
            field=models.CharField(blank=True, max_length=10),
        ),
    ]
