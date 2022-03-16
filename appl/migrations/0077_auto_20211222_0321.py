# Generated by Django 3.2.9 on 2021-12-22 03:21

import appl.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('regis', '0010_applicant_additional_data'),
        ('appl', '0076_auto_20211002_1748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationalprofile',
            name='gpa',
            field=models.FloatField(default=0, help_text='ในกรณีที่กำลังศึกษาชั้นม.6 ให้กรอกเกรดเฉลี่ย 5 ภาคการศึกษา ถ้าจบการศึกษาแล้วให้กรอกเกรดเฉลี่ย 6 ภาคการศึกษา', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(5.0)], verbose_name='GPAX'),
        ),
        migrations.CreateModel(
            name='OldUploadedDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rank', models.IntegerField()),
                ('detail', models.CharField(blank=True, default='', max_length=200)),
                ('uploaded_file', models.FileField(blank=True, upload_to=appl.models.applicant_document_path)),
                ('original_filename', models.CharField(blank=True, max_length=200)),
                ('document_url', models.URLField(blank=True)),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='regis.applicant')),
                ('project_uploaded_document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='old_uploaded_document_set', to='appl.projectuploadeddocument')),
            ],
        ),
    ]