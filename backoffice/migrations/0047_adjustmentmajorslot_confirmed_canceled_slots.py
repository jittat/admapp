# Generated by Django 4.1.13 on 2024-05-05 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backoffice', '0046_alter_projectmenuconfig_menu_flag_json'),
    ]

    operations = [
        migrations.AddField(
            model_name='adjustmentmajorslot',
            name='confirmed_canceled_slots',
            field=models.IntegerField(default=0),
        ),
    ]
