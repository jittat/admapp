from django.test import TestCase

from appl.models import AdmissionProject, Campus, Faculty
from criteria.models import AdmissionCriteria


class AdmissionCriteriaVersioningTestCase(TestCase):
    """Editing a criteria is copy-on-write: it creates a new AdmissionCriteria
    (version N+1) and soft-deletes the old one. Fields that the edit form does
    not re-submit (the curriculum-type and graduate-year flags, which are set
    only via AJAX toggle endpoints) must be carried forward from the old
    version, otherwise they silently reset to their model defaults."""

    def setUp(self):
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test')

        # Version 1 with non-default flags. These flags are normally set via
        # the toggle endpoints, not the create/edit form, so a version bump can
        # only preserve them by copying from the previous version.
        self.criteria_v1 = AdmissionCriteria.objects.create(
            admission_project=self.project,
            faculty=self.faculty,
            version=1,
            accepted_graduate_year_flags='1',
            accepted_student_curriculum_type_flags='2,3')

    def _live_criteria(self):
        return AdmissionCriteria.objects.get(
            admission_project=self.project, is_deleted=False)

    def test_edit_preserves_accepted_graduate_year_flags(self):
        # Imported lazily to avoid a circular import between criteria.views and
        # backoffice at test-module load time.
        from criteria.views import upsert_admission_criteria

        # A minimal POST with one score criteria (an empty submission raises
        # Http404). This drives the edit/version-bump path.
        post = {'required_1_type': 'GPAX', 'required_1_title': 'GPAX'}

        upsert_admission_criteria(post, admission_criteria=self.criteria_v1)

        # Old version is soft-deleted, a new live version N+1 exists.
        self.criteria_v1.refresh_from_db()
        self.assertTrue(self.criteria_v1.is_deleted)

        new_criteria = self._live_criteria()
        self.assertEqual(new_criteria.version, 2)
        self.assertNotEqual(new_criteria.id, self.criteria_v1.id)

        # Regression: the graduate-year flag must survive the version bump.
        self.assertEqual(new_criteria.accepted_graduate_year_flags, '1')
        # Companion flag (already copied before the fix) should also survive.
        self.assertEqual(
            new_criteria.accepted_student_curriculum_type_flags, '2,3')

    def test_edit_persists_additional_admission_upload_fields(self):
        from criteria.views import upsert_admission_criteria

        # The upload-fields editor only appears (and is only parsed) when the
        # project opts in.
        self.project.is_additional_admission_upload_allowed = True
        self.project.save()

        post = {
            'required_1_type': 'GPAX',
            'required_1_title': 'GPAX',
            'additional_admission_upload_fields-1-title': 'แฟ้มสะสมผลงาน',
            'additional_admission_upload_fields-1-descriptions': 'อัพโหลดไฟล์ PDF',
            'additional_admission_upload_fields-1-is_required': '1',
        }

        upsert_admission_criteria(post, admission_criteria=self.criteria_v1)

        new_criteria = self._live_criteria()
        self.assertEqual(new_criteria.version, 2)

        upload_fields = new_criteria.get_additional_admission_upload_fields()
        self.assertEqual(len(upload_fields), 1)
        self.assertEqual(upload_fields[0]['title'], 'แฟ้มสะสมผลงาน')
        self.assertEqual(upload_fields[0]['descriptions'], 'อัพโหลดไฟล์ PDF')
        self.assertTrue(upload_fields[0]['is_required'])
