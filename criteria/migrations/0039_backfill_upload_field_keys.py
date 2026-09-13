import json
import re
import uuid

from django.db import migrations

KEY_RE = re.compile(r'^[0-9a-f]{12}$')


def add_upload_field_keys(rows):
    """Gives every upload-field row a unique stable key; returns whether any
    row changed. Mirrors criteria.views.assign_upload_field_keys."""
    changed = False
    seen = set()
    for row in rows:
        key = row.get('key', '') if isinstance(row, dict) else ''
        if not isinstance(row, dict):
            continue
        if (not isinstance(key, str)) or (not KEY_RE.match(key)) or (key in seen):
            key = uuid.uuid4().hex[:12]
            row['key'] = key
            changed = True
        seen.add(key)
    return changed


def backfill_keys(apps, schema_editor):
    AdmissionCriteria = apps.get_model('criteria', 'AdmissionCriteria')
    criterias = (AdmissionCriteria.objects
                 .exclude(additional_admission_upload_fields_json='')
                 .exclude(additional_admission_upload_fields_json='[]'))
    for criteria in criterias.iterator():
        try:
            rows = json.loads(criteria.additional_admission_upload_fields_json)
        except ValueError:
            continue
        if isinstance(rows, list) and add_upload_field_keys(rows):
            (AdmissionCriteria.objects
             .filter(pk=criteria.pk)
             .update(additional_admission_upload_fields_json=json.dumps(rows)))


class Migration(migrations.Migration):

    dependencies = [
        ('criteria', '0038_admissioncriteria_additional_admission_upload_fields_json'),
    ]

    operations = [
        migrations.RunPython(backfill_keys, migrations.RunPython.noop),
    ]
