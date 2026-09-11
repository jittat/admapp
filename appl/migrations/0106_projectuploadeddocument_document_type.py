from django.db import migrations, models


def set_document_type(apps, schema_editor):
    ProjectUploadedDocument = apps.get_model('appl', 'ProjectUploadedDocument')
    ProjectUploadedDocument.objects.filter(is_url_document=True).update(document_type='url')
    ProjectUploadedDocument.objects.filter(is_url_document=False).update(document_type='file')


def set_is_url_document(apps, schema_editor):
    ProjectUploadedDocument = apps.get_model('appl', 'ProjectUploadedDocument')
    ProjectUploadedDocument.objects.filter(document_type='url').update(is_url_document=True)
    ProjectUploadedDocument.objects.exclude(document_type='url').update(is_url_document=False)


class Migration(migrations.Migration):

    dependencies = [
        ('appl', '0105_admissionproject_is_cupt_export_zero_score_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectuploadeddocument',
            name='document_type',
            field=models.CharField(choices=[('file', 'ไฟล์'), ('url', 'ลิงก์'), ('any', 'ไฟล์หรือลิงก์')], default='file', max_length=10, verbose_name='ชนิดเอกสาร'),
        ),
        migrations.RunPython(set_document_type, set_is_url_document),
        migrations.RemoveField(
            model_name='projectuploadeddocument',
            name='is_url_document',
        ),
    ]
