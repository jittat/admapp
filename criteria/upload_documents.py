"""Turns AdmissionCriteria upload fields into ProjectUploadedDocument slots.

Each upload field (identified by its stable `key`) becomes one slot linked to
the project, shown only to applicants who selected a major covered by the
criteria (`major_numbers`). Run from scripts/sync_criteria_upload_documents.py
or the button on the criteria project index. See docs/uploaded-documents.md.
"""
import logging
from dataclasses import dataclass, field

from django.db import transaction

from appl.models import ProjectUploadedDocument
from criteria.models import AdmissionCriteria

logger = logging.getLogger(__name__)

# Applied to every criteria-generated slot on each sync: change here and re-sync.
DEFAULT_ALLOWED_EXTENSIONS = 'PDF,JPG,JPEG,PNG'
DEFAULT_SIZE_LIMIT = 20_000_000
DEFAULT_SPECIFICATIONS = 'ไฟล์ pdf หรือรูปภาพ (jpg, png) ขนาดไม่เกิน 20MB'

# generated slots are ranked after the hand-made ones
RANK_BASE = 10000

TITLE_MAX_LENGTH = ProjectUploadedDocument._meta.get_field('title').max_length


@dataclass
class SyncSummary:
    created: int = 0
    updated: int = 0
    deleted: int = 0
    unlinked: int = 0
    duplicate_keys: list = field(default_factory=list)
    fields_without_majors: list = field(default_factory=list)

    def as_notice(self):
        notice = (f'ปรับช่องอัพโหลดเอกสารตามเกณฑ์แล้ว: สร้างใหม่ {self.created} '
                  f'แก้ไข {self.updated} ลบ {self.deleted} ยกเลิกการใช้ {self.unlinked}')
        if self.fields_without_majors:
            notice += (' — ไม่พบสาขาของโครงการสำหรับเอกสาร: ' +
                       ', '.join(self.fields_without_majors))
        if self.duplicate_keys:
            notice += ' — พบรหัสเอกสารซ้ำ (ข้าม): ' + ', '.join(self.duplicate_keys)
        return notice


def get_majors_by_cupt_code_id(admission_project):
    majors_by_cupt_code_id = {}
    for major in admission_project.major_set.all():
        if not major.cupt_full_code:
            continue
        cupt_code = major.get_major_cupt_code()
        if cupt_code:
            majors_by_cupt_code_id.setdefault(cupt_code.id, []).append(major)
    return majors_by_cupt_code_id


def get_criteria_majors(admission_criteria, majors_by_cupt_code_id):
    """The project's Majors covered by the criteria, sorted by number.

    CurriculumMajor.major is not populated, so majors are matched through
    their CUPT code, as Major.get_admission_criterias does."""
    majors = {}
    for cmac in admission_criteria.curriculummajoradmissioncriteria_set.select_related('curriculum_major'):
        for major in majors_by_cupt_code_id.get(cmac.curriculum_major.cupt_code_id, []):
            majors[major.number] = major
    return [majors[number] for number in sorted(majors)]


def make_title(title, majors):
    majors_str = ', '.join(major.title for major in majors)
    full_title = f'{title} ({majors_str})'
    if len(full_title) <= TITLE_MAX_LENGTH:
        return full_title

    room = TITLE_MAX_LENGTH - len(title) - len(' (…)')
    if room <= 0:
        return title[:TITLE_MAX_LENGTH]
    return f'{title} ({majors_str[:room]}…)'


def slot_values(upload_field, majors, rank):
    return {
        'title': make_title(upload_field['title'], majors),
        'descriptions': upload_field['descriptions'],
        'specifications': DEFAULT_SPECIFICATIONS,
        'allowed_extentions': DEFAULT_ALLOWED_EXTENSIONS,
        'size_limit': DEFAULT_SIZE_LIMIT,
        'document_type': ProjectUploadedDocument.DOCUMENT_TYPE_ANY,
        'can_have_multiple_files': True,
        'is_required': upload_field['is_required'],
        'is_late_upload_allowed': upload_field['is_late_upload_allowed'],
        'major_numbers': ','.join(str(major.number) for major in majors),
        'rank': rank,
    }


def collect_wanted_slots(admission_project, summary):
    """Maps upload field key -> slot field values for the project's live criteria."""
    wanted = {}
    if not admission_project.is_additional_admission_upload_allowed:
        return wanted

    majors_by_cupt_code_id = get_majors_by_cupt_code_id(admission_project)
    admission_criterias = (AdmissionCriteria.objects
                           .filter(admission_project=admission_project, is_deleted=False)
                           .order_by('faculty_id', 'id'))

    for criteria_index, admission_criteria in enumerate(admission_criterias):
        upload_fields = admission_criteria.get_additional_admission_upload_fields()
        if not upload_fields:
            continue

        majors = get_criteria_majors(admission_criteria, majors_by_cupt_code_id)
        for field_index, upload_field in enumerate(upload_fields):
            key = upload_field['key']
            if key == '' or key in wanted:
                logger.error('duplicate or missing upload field key %r in criteria %s',
                             key, admission_criteria.id)
                summary.duplicate_keys.append(key or upload_field['title'])
                continue
            if not majors:
                summary.fields_without_majors.append(upload_field['title'])
                continue
            wanted[key] = slot_values(upload_field, majors,
                                      RANK_BASE + criteria_index * 10 + field_index)
    return wanted


def has_uploads(project_uploaded_document):
    return (project_uploaded_document.uploaded_document_set.exists() or
            project_uploaded_document.old_uploaded_document_set.exists())


@transaction.atomic
def sync_criteria_upload_documents(admission_project):
    summary = SyncSummary()
    wanted = collect_wanted_slots(admission_project, summary)

    linked = {doc.criteria_upload_key: doc
              for doc in (ProjectUploadedDocument.objects
                          .filter(admission_projects=admission_project)
                          .exclude(criteria_upload_key=''))}

    for key, values in wanted.items():
        doc = linked.get(key)
        is_linked = doc is not None
        if doc is None:
            # a slot unlinked by an earlier sync comes back with its uploads
            doc = (ProjectUploadedDocument.objects
                   .filter(criteria_upload_key=key, admission_projects__isnull=True)
                   .first())

        if doc is None:
            doc = ProjectUploadedDocument(criteria_upload_key=key, **values)
            doc.save()
            doc.admission_projects.add(admission_project)
            summary.created += 1
            continue

        changed = [name for name, value in values.items() if getattr(doc, name) != value]
        for name in changed:
            setattr(doc, name, values[name])
        if changed:
            doc.save()
        if not is_linked:
            doc.admission_projects.add(admission_project)
        if changed or not is_linked:
            summary.updated += 1

    for key, doc in linked.items():
        if key in wanted:
            continue
        if has_uploads(doc) or doc.admission_projects.count() > 1:
            doc.admission_projects.remove(admission_project)
            doc.major_numbers = ''
            doc.save()
            summary.unlinked += 1
        else:
            doc.delete()
            summary.deleted += 1

    return summary
