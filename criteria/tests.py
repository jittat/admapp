from decimal import Decimal

from django.http import Http404
from django.test import TestCase

from appl.models import AdmissionProject, Campus, Faculty
from criteria.models import (AdmissionCriteria, ScoreCriteria, CurriculumMajor,
                             CurriculumMajorAdmissionCriteria, MajorCuptCode)


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


class UpsertAdmissionCriteriaWritePathTestCase(TestCase):
    """The create/edit views funnel through upsert_admission_criteria, which
    parses the flat POST into score criteria + selected majors and writes them
    (copy-on-write on edit). These cover the write side end to end."""

    def setUp(self):
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test')
        self.cupt = MajorCuptCode.objects.create(
            program_code='0001', program_type='ปกติ', program_type_code='A',
            faculty=self.faculty, major_code='', title='วิศวกรรมคอมพิวเตอร์',
            major_title='')
        self.curriculum_major = CurriculumMajor.objects.create(
            admission_project=self.project, cupt_code=self.cupt,
            faculty=self.faculty)

    def _live_criteria(self):
        return AdmissionCriteria.objects.get(
            admission_project=self.project, is_deleted=False)

    def test_create_builds_score_and_major_criteria(self):
        from criteria.views import upsert_admission_criteria

        post = {
            'required_1_type': 'GPAX', 'required_1_title': 'GPAX',
            'required_1_value': '2.50',
            'scoring_1_type': 'TGAT', 'scoring_1_title': 'TGAT',
            'scoring_1_value': '70',
            'scoring_1.1_type': 'TGAT1', 'scoring_1.1_title': 'TGAT1',
            'scoring_1.1_value': '30',
            'majors_1_id': str(self.curriculum_major.id), 'majors_1_slot': '10',
        }

        upsert_admission_criteria(post, project=self.project, faculty=self.faculty)

        criteria = self._live_criteria()
        self.assertEqual(criteria.version, 1)
        self.assertEqual(criteria.faculty_id, self.faculty.id)

        # Required primary criteria.
        required = criteria.scorecriteria_set.get(criteria_type='required')
        self.assertEqual(required.description, 'GPAX')
        self.assertEqual(required.value, Decimal('2.50'))

        # Scoring primary + its secondary child, correctly parented.
        scoring_primary = criteria.scorecriteria_set.get(
            criteria_type='scoring', secondary_order=0)
        self.assertEqual(scoring_primary.description, 'TGAT')
        child = criteria.scorecriteria_set.get(secondary_order=1)
        self.assertEqual(child.description, 'TGAT1')
        self.assertEqual(child.parent_id, scoring_primary.id)

        # Selected major.
        major_criteria = criteria.curriculummajoradmissioncriteria_set.get()
        self.assertEqual(major_criteria.curriculum_major_id, self.curriculum_major.id)
        self.assertEqual(major_criteria.slots, 10)
        # Denormalized snapshot is written.
        self.assertIn('0001', criteria.curriculum_majors_json)

    def test_create_records_created_by_user(self):
        from criteria.views import upsert_admission_criteria

        class FakeUser:
            username = 'staff01'

        post = {'required_1_type': 'GPAX', 'required_1_title': 'GPAX'}
        upsert_admission_criteria(post, project=self.project, faculty=self.faculty,
                                  user=FakeUser())

        self.assertEqual(self._live_criteria().created_by, 'staff01')

    def test_empty_submission_raises_http404(self):
        from criteria.views import upsert_admission_criteria

        with self.assertRaises(Http404):
            upsert_admission_criteria({}, project=self.project, faculty=self.faculty)
        self.assertFalse(
            AdmissionCriteria.objects.filter(admission_project=self.project).exists())

    def test_edit_carries_add_limit_from_previous_version(self):
        from criteria.views import upsert_admission_criteria

        base_post = {
            'required_1_type': 'GPAX', 'required_1_title': 'GPAX',
            'majors_1_id': str(self.curriculum_major.id), 'majors_1_slot': '5',
        }
        upsert_admission_criteria(base_post, project=self.project, faculty=self.faculty)
        v1 = self._live_criteria()

        # add_limit is set outside the create/edit form (its own endpoint).
        mc = v1.curriculummajoradmissioncriteria_set.get()
        mc.add_limit = 'C7'
        mc.save()

        upsert_admission_criteria(base_post, admission_criteria=v1)

        v2 = self._live_criteria()
        self.assertEqual(v2.version, 2)
        new_mc = v2.curriculummajoradmissioncriteria_set.get()
        self.assertEqual(new_mc.add_limit, 'C7')


class CriteriaViewHelpersTestCase(TestCase):
    """The pure helpers extracted from render_create/render_edit_criteria."""

    def setUp(self):
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test')

    def _cupt(self, program_code, title, major_title=''):
        return MajorCuptCode.objects.create(
            program_code=program_code, program_type='ปกติ', program_type_code='A',
            faculty=self.faculty, major_code='', title=title, major_title=major_title)

    def _curriculum_major(self, cupt):
        return CurriculumMajor.objects.create(
            admission_project=self.project, cupt_code=cupt, faculty=self.faculty)

    def test_score_criterias_to_data_splits_and_nests(self):
        from criteria.views import score_criterias_to_data

        criteria = AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1)
        ScoreCriteria.objects.create(
            admission_criteria=criteria, primary_order=1, secondary_order=0,
            criteria_type='required', score_type='GPAX', description='GPAX')
        scoring = ScoreCriteria.objects.create(
            admission_criteria=criteria, primary_order=1, secondary_order=0,
            criteria_type='scoring', score_type='TGAT', description='TGAT',
            value=Decimal('70'))
        ScoreCriteria.objects.create(
            admission_criteria=criteria, primary_order=1, secondary_order=1,
            criteria_type='scoring', score_type='TGAT1', description='TGAT1',
            parent=scoring)

        primary = criteria.scorecriteria_set.filter(secondary_order=0)
        data_required, data_scoring = score_criterias_to_data(primary)

        self.assertEqual(len(data_required), 1)
        self.assertEqual(data_required[0]['title'], 'GPAX')

        self.assertEqual(len(data_scoring), 1)
        self.assertEqual(data_scoring[0]['title'], 'TGAT')
        self.assertEqual(data_scoring[0]['value'], 70.0)
        self.assertEqual(len(data_scoring[0]['children']), 1)
        self.assertEqual(data_scoring[0]['children'][0]['title'], 'TGAT1')

    def test_majors_to_json_is_sorted_by_program_code(self):
        import json
        from criteria.views import majors_to_json

        cm_b = self._curriculum_major(self._cupt('0002', 'ข', major_title='ข'))
        cm_a = self._curriculum_major(self._cupt('0001', 'ก', major_title='ก'))

        data = json.loads(majors_to_json([cm_b, cm_a]))

        self.assertEqual([d['id'] for d in data], [cm_a.id, cm_b.id])
        self.assertIn('ก', data[0]['title'])

    def test_additional_fields_context_create_is_empty(self):
        from criteria.views import additional_fields_context

        self.project.is_additional_admission_form_allowed = True
        self.project.is_additional_admission_upload_allowed = True

        ctx = additional_fields_context(self.project)

        self.assertTrue(ctx['has_additional_form_fields'])
        self.assertTrue(ctx['has_additional_upload_fields'])
        self.assertEqual(ctx['additional_form_fields'], [])
        self.assertEqual(ctx['additional_upload_fields'], [])
        self.assertEqual(ctx['additional_notice'], '')

    def test_additional_fields_context_edit_loads_values(self):
        from criteria.views import additional_fields_context

        criteria = AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1,
            additional_admission_upload_fields_json=(
                '[{"title": "doc", "descriptions": "d", "is_required": true}]'),
            additional_notice='hello')

        ctx = additional_fields_context(self.project, criteria)

        self.assertEqual(len(ctx['additional_upload_fields']), 1)
        self.assertEqual(ctx['additional_upload_fields'][0]['title'], 'doc')
        self.assertEqual(ctx['additional_notice'], 'hello')


class ExtractAdditionalFieldsTestCase(TestCase):
    """The POST-parsing extractors and their project gating."""

    def setUp(self):
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test')

    def test_indexed_rows_skips_blank_titles_and_applies_transforms(self):
        from criteria.views import extract_indexed_rows_as_json
        import json

        post = {
            'f-1-title': ' A ', 'f-1-size': ' short ',
            'f-2-title': '   ',  # blank -> skipped
            'f-3-title': 'B', 'f-3-flag': 'x',
        }
        rows = json.loads(extract_indexed_rows_as_json(
            post, 'f', {'size': lambda v: v.strip(),
                        'flag': lambda v: v != ''}))

        titles = sorted(r['title'] for r in rows)
        self.assertEqual(titles, ['A', 'B'])
        row_a = next(r for r in rows if r['title'] == 'A')
        self.assertEqual(row_a['size'], 'short')
        self.assertFalse(row_a['flag'])  # missing key defaults to '' -> False

    def test_upload_fields_gated_off_returns_empty(self):
        from criteria.views import extract_additional_admission_upload_fields_as_json

        self.project.is_additional_admission_upload_allowed = False
        post = {'additional_admission_upload_fields-1-title': 'doc'}
        self.assertEqual(
            extract_additional_admission_upload_fields_as_json(self.project, post), '')

    def test_upload_fields_gated_on_parses_rows(self):
        from criteria.views import extract_additional_admission_upload_fields_as_json
        import json

        self.project.is_additional_admission_upload_allowed = True
        post = {
            'additional_admission_upload_fields-1-title': 'doc',
            'additional_admission_upload_fields-1-descriptions': 'desc',
            'additional_admission_upload_fields-1-is_required': '1',
        }
        rows = json.loads(
            extract_additional_admission_upload_fields_as_json(self.project, post))
        self.assertEqual(rows, [{'title': 'doc', 'descriptions': 'desc',
                                 'is_required': True}])
