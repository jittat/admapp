import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.http import Http404
from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from appl.models import AdmissionProject, AdmissionRound, Campus, Faculty
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
        self.project.is_additional_admission_late_upload_allowed = True
        self.project.save()

        post = {
            'required_1_type': 'GPAX',
            'required_1_title': 'GPAX',
            'additional_admission_upload_fields-1-title': 'แฟ้มสะสมผลงาน',
            'additional_admission_upload_fields-1-descriptions': 'อัพโหลดไฟล์ PDF',
            'additional_admission_upload_fields-1-is_required': '1',
            'additional_admission_upload_fields-1-is_late_upload_allowed': '1',
        }

        upsert_admission_criteria(post, admission_criteria=self.criteria_v1)

        new_criteria = self._live_criteria()
        self.assertEqual(new_criteria.version, 2)

        upload_fields = new_criteria.get_additional_admission_upload_fields()
        self.assertEqual(len(upload_fields), 1)
        self.assertEqual(upload_fields[0]['title'], 'แฟ้มสะสมผลงาน')
        self.assertEqual(upload_fields[0]['descriptions'], 'อัพโหลดไฟล์ PDF')
        self.assertTrue(upload_fields[0]['is_required'])
        self.assertTrue(upload_fields[0]['is_late_upload_allowed'])


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
        # late uploads need their own opt-in on top of the upload flag
        self.assertFalse(ctx['has_additional_late_upload_fields'])
        self.project.is_additional_admission_late_upload_allowed = True
        self.assertTrue(additional_fields_context(
            self.project)['has_additional_late_upload_fields'])
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
                                 'is_required': True,
                                 'is_late_upload_allowed': False}])

    def test_upload_fields_late_upload_checkbox_requires_project_flag(self):
        from criteria.views import extract_additional_admission_upload_fields_as_json
        import json

        self.project.is_additional_admission_upload_allowed = True
        post = {
            'additional_admission_upload_fields-1-title': 'doc',
            'additional_admission_upload_fields-1-is_late_upload_allowed': '1',
        }

        # The project does not allow late uploads: the checkbox is not rendered,
        # and a submitted value is forced to False (so turning the flag off and
        # re-saving clears stale values).
        rows = json.loads(
            extract_additional_admission_upload_fields_as_json(self.project, post))
        self.assertFalse(rows[0]['is_late_upload_allowed'])

        self.project.is_additional_admission_late_upload_allowed = True
        rows = json.loads(
            extract_additional_admission_upload_fields_as_json(self.project, post))
        self.assertTrue(rows[0]['is_late_upload_allowed'])


ADDITIONAL_FORM_FIELDS_COL_TEMPLATE = (
    'criteria/include/scorecriteria_col_additional_form_fields.html')


class AdditionalFormFieldsEditLinkTestCase(TestCase):
    """The 'คำถามเพิ่มเติม' section of the criteria index offers links into
    edit-form-fields. They must follow the same gates as every other edit
    control on the page: is_criteria_edit_allowed (the project flag, OR'd with
    super-admin by the view) and is_edit_link_hidden (set by read-only pages)."""

    def setUp(self):
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test',
            is_additional_admission_form_allowed=True)
        self.admission_round = AdmissionRound.objects.create(
            number=1, rank=1, acceptance_result_date=datetime.date(2026, 1, 1))

        self.criteria_with_fields = AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1,
            additional_admission_form_fields_json=(
                '[{"title": "เหตุผลที่เลือกสาขานี้", "size": "short"}]'))
        self.criteria_without_fields = AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1)

    def _render(self, admission_criteria, **context):
        return render_to_string(ADDITIONAL_FORM_FIELDS_COL_TEMPLATE,
                                {'project': self.project,
                                 'admission_round': self.admission_round,
                                 'admission_criteria': admission_criteria,
                                 **context})

    def _edit_url(self, admission_criteria):
        return reverse('backoffice:criteria:edit-form-fields',
                       args=[self.project.id, self.admission_round.id,
                             admission_criteria.id])

    def test_edit_link_shown_when_criteria_edit_allowed(self):
        html = self._render(self.criteria_with_fields,
                            is_criteria_edit_allowed=True)

        self.assertIn(self._edit_url(self.criteria_with_fields), html)
        # The questions themselves are shown either way.
        self.assertIn('เหตุผลที่เลือกสาขานี้', html)

    def test_edit_link_hidden_when_criteria_edit_not_allowed(self):
        html = self._render(self.criteria_with_fields,
                            is_criteria_edit_allowed=False)

        self.assertNotIn(self._edit_url(self.criteria_with_fields), html)
        # The existing questions are data, not an edit affordance: still shown.
        self.assertIn('เหตุผลที่เลือกสาขานี้', html)

    def test_edit_link_hidden_when_context_flag_missing(self):
        # Read-only pages (e.g. report_index) share this include and pass no
        # is_criteria_edit_allowed at all, which must fail closed.
        html = self._render(self.criteria_with_fields)

        self.assertNotIn(self._edit_url(self.criteria_with_fields), html)

    def test_edit_link_hidden_when_edit_links_hidden(self):
        html = self._render(self.criteria_with_fields,
                            is_criteria_edit_allowed=True,
                            is_edit_link_hidden=True)

        self.assertNotIn(self._edit_url(self.criteria_with_fields), html)

    def test_add_link_shown_when_criteria_edit_allowed(self):
        html = self._render(self.criteria_without_fields,
                            is_criteria_edit_allowed=True)

        self.assertIn(self._edit_url(self.criteria_without_fields), html)
        self.assertIn('เพิ่มคำถาม', html)

    def test_add_card_hidden_when_criteria_edit_not_allowed(self):
        # With no questions to show, the whole card is only an edit affordance.
        html = self._render(self.criteria_without_fields,
                            is_criteria_edit_allowed=False)

        self.assertNotIn(self._edit_url(self.criteria_without_fields), html)
        self.assertNotIn('เพิ่มคำถาม', html)
        self.assertEqual(html.strip(), '')


class AdditionalUploadFieldsAndNoticeDisplayTestCase(TestCase):
    """The upload-fields and notice panels on the criteria index are collapsed
    notes for manual checking. They must render nothing when their field is
    empty (so they cost no space in the common case), and must show up on
    stored content even when the project flag that authored it is now off."""

    TEMPLATE = 'criteria/include/scorecriteria_col_additional_info.html'

    def setUp(self):
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test',
            is_additional_admission_upload_allowed=True)

    def _criteria(self, **fields):
        return AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1,
            **fields)

    def _render(self, admission_criteria):
        return render_to_string(self.TEMPLATE,
                                {'project': self.project,
                                 'admission_criteria': admission_criteria})

    def test_renders_nothing_when_both_fields_are_empty(self):
        html = self._render(self._criteria())

        self.assertEqual(html.strip(), '')

    def test_upload_fields_show_rows_in_a_collapsed_panel(self):
        criteria = self._criteria(
            additional_admission_upload_fields_json=(
                '[{"title": "แฟ้มสะสมผลงาน", "descriptions": "ไฟล์ PDF",'
                ' "is_required": true},'
                ' {"title": "ใบรับรอง", "descriptions": "", "is_required": false}]'))

        html = self._render(criteria)

        self.assertIn('<strong>อัพโหลดเพิ่มเติม</strong> (2)', html)
        self.assertIn('แฟ้มสะสมผลงาน', html)
        self.assertIn('ใบรับรอง', html)
        # Collapsed by default, keyed per criteria so rows do not collide.
        self.assertIn('additionalUploadFieldsId-%d' % criteria.id, html)
        self.assertIn('class="collapse"', html)
        # No notice stored: only the upload note is offered.
        self.assertNotIn('รายละเอียดเพิ่มเติม', html)

    def test_upload_fields_late_upload_column_follows_project_flag(self):
        criteria = self._criteria(
            additional_admission_upload_fields_json=(
                '[{"title": "แฟ้มสะสมผลงาน", "is_required": true,'
                ' "is_late_upload_allowed": true}]'))

        html = self._render(criteria)
        self.assertNotIn('หลังหมดเขต', html)

        self.project.is_additional_admission_late_upload_allowed = True
        html = self._render(criteria)
        self.assertIn('หลังหมดเขต', html)
        self.assertIn('อัพโหลดได้', html)

    def test_upload_fields_shown_even_when_project_flag_is_off(self):
        # Stored content with the flag since turned off is the anomaly a manual
        # check needs to see (the next edit would silently blank it).
        self.project.is_additional_admission_upload_allowed = False
        criteria = self._criteria(
            additional_admission_upload_fields_json=(
                '[{"title": "แฟ้มสะสมผลงาน", "is_required": true}]'))

        html = self._render(criteria)

        self.assertIn('แฟ้มสะสมผลงาน', html)

    def test_notice_shows_text_in_a_collapsed_panel(self):
        criteria = self._criteria(additional_notice='บรรทัดแรก\nบรรทัดที่สอง')

        html = self._render(criteria)

        self.assertIn('รายละเอียดเพิ่มเติม', html)
        self.assertIn('บรรทัดแรก<br>บรรทัดที่สอง', html)
        self.assertIn('additionalNoticeId-%d' % criteria.id, html)
        self.assertIn('class="collapse"', html)
        self.assertNotIn('อัพโหลดเพิ่มเติม', html)

    def test_notice_shown_even_when_project_flag_is_off(self):
        self.project.is_additional_notice_allowed = False
        criteria = self._criteria(additional_notice='ประกาศ')

        self.assertIn('ประกาศ', self._render(criteria))

    def test_both_notes_share_one_line_with_panels_below(self):
        criteria = self._criteria(
            additional_admission_upload_fields_json=(
                '[{"title": "แฟ้มสะสมผลงาน", "is_required": true}]'),
            additional_notice='ประกาศ')

        html = self._render(criteria)

        # The whole section is one card, matching the questions card above it.
        self.assertIn('additionalInfoId-%d' % criteria.id, html)
        self.assertIn('class="card mt-1"', html)
        # Both notes sit in the single wrapper div that opens the partial, and
        # both collapse panels follow it.
        self.assertLess(html.index('อัพโหลดเพิ่มเติม'), html.index('รายละเอียดเพิ่มเติม'))
        self.assertLess(html.index('รายละเอียดเพิ่มเติม'),
                        html.index('id="additionalUploadFieldsId-%d"' % criteria.id))

    def test_django_comment_is_not_rendered(self):
        # {# #} cannot span multiple lines; the multi-line form leaks into the
        # page as literal text, so the header comment uses {% comment %}.
        html = self._render(self._criteria(additional_notice='ประกาศ'))

        self.assertNotIn('manual check', html)
        self.assertNotIn('#}', html)


class EditAdditionalFormFieldsPermissionTestCase(TestCase):
    """edit_additional_admission_form_fields saves in place with no version
    bump, so it must refuse when the project has criteria editing locked --
    the same guard handle_create_criteria / handle_edit_criteria apply."""

    def setUp(self):
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test',
            is_additional_admission_form_allowed=True,
            is_criteria_edit_allowed=False)
        self.admission_round = AdmissionRound.objects.create(
            number=1, rank=1, acceptance_result_date=datetime.date(2026, 1, 1))
        self.criteria = AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1)

        self.url = reverse('backoffice:criteria:edit-form-fields',
                           args=[self.project.id, self.admission_round.id,
                                 self.criteria.id])

        self.user = self._staff_user('faculty01')

    def _staff_user(self, username, is_super_admin=False):
        # A Profile is auto-created by a post_save signal on User.
        user = User.objects.create_user(username=username, password='x',
                                        is_staff=is_super_admin)
        user.profile.faculty = self.faculty
        user.profile.save()
        user.profile.admission_projects.add(self.project)
        return user

    def _post_a_question(self):
        return self.client.post(self.url, {
            'additional_admission_form_fields-1-title': 'คำถามใหม่',
            'additional_admission_form_fields-1-size': 'short',
        })

    def test_get_forbidden_when_criteria_edit_not_allowed(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 403)

    def test_post_does_not_save_when_criteria_edit_not_allowed(self):
        self.client.force_login(self.user)

        response = self._post_a_question()

        self.assertEqual(response.status_code, 403)
        self.criteria.refresh_from_db()
        self.assertEqual(self.criteria.get_additional_admission_form_fields(), [])

    def test_post_saves_when_criteria_edit_allowed(self):
        self.project.is_criteria_edit_allowed = True
        self.project.save()
        self.client.force_login(self.user)

        response = self._post_a_question()

        self.assertEqual(response.status_code, 200)
        self.criteria.refresh_from_db()
        fields = self.criteria.get_additional_admission_form_fields()
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]['title'], 'คำถามใหม่')

    def test_super_admin_can_edit_when_criteria_edit_not_allowed(self):
        # is_criteria_edit_allowed is OR'd with super-admin everywhere else.
        self.client.force_login(self._staff_user('admin01', is_super_admin=True))

        response = self._post_a_question()

        self.assertEqual(response.status_code, 200)
        self.criteria.refresh_from_db()
        self.assertEqual(
            len(self.criteria.get_additional_admission_form_fields()), 1)

    def test_forbidden_when_additional_form_not_allowed_by_project(self):
        # Pre-existing gate, kept ahead of the new one.
        self.project.is_criteria_edit_allowed = True
        self.project.is_additional_admission_form_allowed = False
        self.project.save()
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(self.url).status_code, 403)


class FacultyScopeAuthorizationTestCase(TestCase):
    """Edit endpoints authorize on the *criteria's own* faculty, not on the
    faculty currently selected in the UI. A campus admin manages every faculty
    in their campus, and most of these URLs carry no ?faculty_id= at all, so
    comparing against extract_user_faculty's fallback (faculty_choices[0])
    locked campus admins out of every faculty but the first."""

    def setUp(self):
        self.campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.other_campus = Campus.objects.create(title='Sriracha', short_title='SR')

        # deliberately not the first faculty of the campus by id
        self.first_faculty = Faculty.objects.create(title='Engineering',
                                                    campus=self.campus)
        self.faculty = Faculty.objects.create(title='Science',
                                              campus=self.campus)
        self.other_campus_faculty = Faculty.objects.create(title='Economics',
                                                           campus=self.other_campus)

        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test',
            is_additional_admission_form_allowed=True,
            is_criteria_edit_allowed=True)
        self.admission_round = AdmissionRound.objects.create(
            number=1, rank=1, acceptance_result_date=datetime.date(2026, 1, 1))
        self.criteria = AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1)

        self.form_fields_url = reverse(
            'backoffice:criteria:edit-form-fields',
            args=[self.project.id, self.admission_round.id, self.criteria.id])
        self.curriculum_type_url = reverse(
            'backoffice:criteria:update-accepted-curriculum-type',
            args=[self.project.id, self.admission_round.id, self.criteria.id, 1])

    def _user(self, username, faculty=None, is_campus_admin=False,
              campus=None, is_admission_admin=False):
        # A Profile is auto-created by a post_save signal on User.
        user = User.objects.create_user(username=username, password='x')
        user.profile.faculty = faculty
        user.profile.is_campus_admin = is_campus_admin
        user.profile.campus = campus
        user.profile.is_admission_admin = is_admission_admin
        user.profile.save()
        user.profile.admission_projects.add(self.project)
        return user

    def _campus_admin(self):
        return self._user('campus01', is_campus_admin=True, campus=self.campus)

    def test_campus_admin_can_open_form_fields_of_any_faculty_in_campus(self):
        # no ?faculty_id= -- extract_user_faculty would pick first_faculty
        self.client.force_login(self._campus_admin())

        response = self.client.get(self.form_fields_url)

        self.assertEqual(response.status_code, 200)

    def test_campus_admin_can_toggle_curriculum_type_of_any_faculty_in_campus(self):
        self.client.force_login(self._campus_admin())

        response = self.client.post(self.curriculum_type_url)

        self.assertEqual(response.status_code, 200)
        self.criteria.refresh_from_db()
        self.assertNotEqual(self.criteria.accepted_student_curriculum_type_flags,
                            AdmissionCriteria.INITIAL_CURR_TYPE_FLAG)

    def test_campus_admin_cannot_edit_faculty_in_another_campus(self):
        self.criteria.faculty = self.other_campus_faculty
        self.criteria.save()
        self.client.force_login(self._campus_admin())

        response = self.client.post(self.curriculum_type_url)

        self.assertEqual(response.status_code, 302)
        self.criteria.refresh_from_db()
        self.assertEqual(self.criteria.accepted_student_curriculum_type_flags,
                         AdmissionCriteria.INITIAL_CURR_TYPE_FLAG)

    def test_faculty_user_cannot_edit_another_faculty(self):
        self.client.force_login(self._user('faculty01',
                                           faculty=self.first_faculty))

        response = self.client.post(self.curriculum_type_url)

        self.assertEqual(response.status_code, 302)
        self.criteria.refresh_from_db()
        self.assertEqual(self.criteria.accepted_student_curriculum_type_flags,
                         AdmissionCriteria.INITIAL_CURR_TYPE_FLAG)

    def test_faculty_user_can_edit_own_faculty(self):
        self.client.force_login(self._user('faculty02', faculty=self.faculty))

        response = self.client.post(self.curriculum_type_url)

        self.assertEqual(response.status_code, 200)

    def test_admission_admin_can_edit_any_faculty(self):
        self.criteria.faculty = self.other_campus_faculty
        self.criteria.save()
        self.client.force_login(self._user('admin01', is_admission_admin=True))

        response = self.client.post(self.curriculum_type_url)

        self.assertEqual(response.status_code, 200)

    def test_project_index_falls_back_when_faculty_id_is_cross_campus(self):
        # extract_user_faculty returns None here; the page must not blow up.
        self.client.force_login(self._campus_admin())
        url = reverse('backoffice:criteria:project-index',
                      args=[self.project.id, self.admission_round.id])

        response = self.client.get(url,
                                   {'faculty_id': self.other_campus_faculty.id})

        self.assertEqual(response.status_code, 200)


class PortfolioInterviewPercentTestCase(SimpleTestCase):
    """Portfolio projects report two scoring columns to CUPT, portfolio and
    interview. The split is derived from the top-level scoring criteria the
    faculty authored: everything that is not interview weight is portfolio
    weight, normalized to 100."""

    def _percents(self, items):
        # Imported inside the test: importing criteria.views at module scope
        # trips the circular import with backoffice.decorators.
        from criteria.views.cuptexport import compute_portfolio_interview_percents
        return compute_portfolio_interview_percents(items)

    def _item(self, score_type, base_weight, description='', **extra):
        item = {'score_type': score_type,
                'description': description,
                'base_weight': base_weight}
        item.update(extra)
        return item

    def test_interview_recognized_by_score_type(self):
        portfolio, interview, _ = self._percents([
            self._item('PORTFORLIO', 70.0, 'คะแนนแฟ้มผลงาน'),
            self._item('INTERVIEW', 30.0, 'การสอบสัมภาษณ์'),
        ])

        self.assertEqual((portfolio, interview), (70, 30))

    def test_english_interview_counts_as_interview(self):
        portfolio, interview, _ = self._percents([
            self._item('PORTFORLIO', 80.0),
            self._item('INTERVIEW_ENGLISH', 20.0),
        ])

        self.assertEqual((portfolio, interview), (80, 20))

    def test_interview_recognized_by_description(self):
        # Free-text criteria keep score_type OTHER, so the Thai word is the
        # only signal.
        portfolio, interview, _ = self._percents([
            self._item('OTHER', 75.0, 'แฟ้มสะสมผลงาน'),
            self._item('OTHER', 25.0, 'คะแนนการสอบสัมภาษณ์'),
        ])

        self.assertEqual((portfolio, interview), (75, 25))

    def test_weights_are_normalized_to_100(self):
        portfolio, interview, _ = self._percents([
            self._item('PORTFORLIO', 30.0),
            self._item('INTERVIEW', 10.0),
        ])

        self.assertEqual((portfolio, interview), (75, 25))

    def test_rounding_remainder_goes_to_portfolio(self):
        portfolio, interview, messages = self._percents([
            self._item('PORTFORLIO', 2.0),
            self._item('INTERVIEW', 1.0),
        ])

        self.assertEqual((portfolio, interview), (67, 33))
        self.assertEqual(portfolio + interview, 100)
        self.assertTrue(any('rounded' in m for m in messages))

    def test_max_group_is_judged_by_the_group_row_not_its_children(self):
        # The group row itself is interview; its children are not.
        group = self._item('GROUP-MAX', 40.0, 'การสอบสัมภาษณ์ (ใช้คะแนนมากที่สุด)',
                           group_score_type='OTHER',
                           children=[{'score_type': 'TGAT', 'value': 1}])

        portfolio, interview, _ = self._percents([
            self._item('PORTFORLIO', 60.0),
            group,
        ])

        self.assertEqual((portfolio, interview), (60, 40))

    def test_max_group_of_interview_children_is_not_interview_by_itself(self):
        group = self._item('GROUP-MAX', 40.0, 'ใช้คะแนนมากที่สุด',
                           group_score_type='OTHER',
                           children=[{'score_type': 'INTERVIEW', 'value': 1}])

        portfolio, interview, _ = self._percents([
            self._item('PORTFORLIO', 60.0),
            group,
        ])

        self.assertEqual((portfolio, interview), (100, 0))

    def test_max_group_tagged_as_interview_counts_as_interview(self):
        group = self._item('GROUP-MAX', 40.0, 'ใช้คะแนนมากที่สุด',
                           group_score_type='INTERVIEW',
                           children=[])

        portfolio, interview, _ = self._percents([
            self._item('PORTFORLIO', 60.0),
            group,
        ])

        self.assertEqual((portfolio, interview), (60, 40))

    def test_all_interview_gives_zero_portfolio(self):
        portfolio, interview, _ = self._percents([
            self._item('INTERVIEW', 100.0),
        ])

        self.assertEqual((portfolio, interview), (0, 100))

    def test_no_scoring_weights_gives_zero_zero(self):
        portfolio, interview, messages = self._percents([])

        self.assertEqual((portfolio, interview), (0, 0))
        self.assertTrue(any('0/0' in m for m in messages))

    def test_preprocess_replaces_extracted_scoring_criteria(self):
        from criteria.views.cuptexport import preprocess_portfolio_admission_criteria

        class FakeCriteria:
            pass

        criteria = FakeCriteria()
        criteria.extracted_scoring_criteria = ([
            self._item('PORTFORLIO', 70.0),
            self._item('INTERVIEW', 30.0),
        ], ['earlier message'])

        preprocess_portfolio_admission_criteria(None, [criteria])

        items, messages = criteria.extracted_scoring_criteria
        self.assertEqual(items, [
            {'score_type': 'R1_PORTFOLIO', 'base_weight': 70.0},
            {'score_type': 'R1_INTERVIEW', 'base_weight': 30.0},
        ])
        self.assertIn('earlier message', messages)

    def test_preprocess_handles_criteria_with_no_extraction(self):
        from criteria.views.cuptexport import preprocess_portfolio_admission_criteria

        class FakeCriteria:
            pass

        criteria = FakeCriteria()

        preprocess_portfolio_admission_criteria(None, [criteria])

        items, _ = criteria.extracted_scoring_criteria
        self.assertEqual([i['base_weight'] for i in items], [0.0, 0.0])


class CriteriaAsStrTestCase(TestCase):
    """criteria_as_str renders a criteria list to text, in four combinable
    modes: plain vs. numbered, percent-shown vs. description-only
    (hide_percent), and an optional display_fn that overrides both. It backs
    get_all_required/scoring_score_criteria_as_str (unnumbered, used by the
    validation page) and get_all_scoring_score_criteria_as_numbered_str
    (numbered, used for the folio_criteria CUPT export column), and is also
    what scripts/export_majors_from_criteria.py's render_score_criterias
    delegates to."""

    def setUp(self):
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        faculty = Faculty.objects.create(title='Engineering', campus=campus)
        project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test')
        self.admission_criteria = AdmissionCriteria.objects.create(
            admission_project=project, faculty=faculty, version=1)

        # A plain item with no children.
        self.parent1 = ScoreCriteria.objects.create(
            admission_criteria=self.admission_criteria,
            primary_order=1, secondary_order=0,
            criteria_type='scoring', score_type='GPAX',
            value=Decimal('60.00'), description='GPAX')

        # A group item with one child, exercising the indented-child path.
        self.parent2 = ScoreCriteria.objects.create(
            admission_criteria=self.admission_criteria,
            primary_order=2, secondary_order=0,
            criteria_type='scoring', score_type='GROUP-MAX',
            value=Decimal('40.00'), description='วิชาเฉพาะ', relation='MAX')
        self.child = ScoreCriteria.objects.create(
            admission_criteria=self.admission_criteria,
            primary_order=2, secondary_order=1,
            criteria_type='scoring', score_type='TGAT',
            value=Decimal('40.00'), description='TGAT', parent=self.parent2)

        self.criteria = [self.parent1, self.parent2]

    def test_default_matches_plain_str_join_with_dash_indented_children(self):
        from criteria.models.admission_criteria import criteria_as_str

        result = criteria_as_str(self.criteria)

        self.assertEqual(result, '\n'.join([
            str(self.parent1),
            str(self.parent2),
            '  - ' + str(self.child),
        ]))

    def test_numbered_shows_percent_with_given_indent(self):
        from criteria.models.admission_criteria import criteria_as_str

        result = criteria_as_str(self.criteria, numbered=True, indent_chars='    ')

        self.assertEqual(result, '\n'.join([
            f'1. {self.parent1}',
            f'2. {self.parent2}',
            f'    2.1 {self.child}',
        ]))

    def test_hide_percent_uses_description_only(self):
        from criteria.models.admission_criteria import criteria_as_str

        result = criteria_as_str(self.criteria, numbered=True, hide_percent=True,
                                 indent_chars='    ')

        self.assertEqual(result, '\n'.join([
            f'1. {self.parent1.description}',
            f'2. {self.parent2.description}',
            f'    2.1 {self.child.description}',
        ]))

    def test_display_fn_overrides_hide_percent(self):
        # display_fn wins even when hide_percent is also set, since
        # render_score_criterias(short=True) relies on this to fall through
        # to display_with_short_relation() instead of .description.
        from criteria.models.admission_criteria import criteria_as_str

        result = criteria_as_str(
            self.criteria, numbered=True, hide_percent=True, indent_chars='    ',
            display_fn=lambda c: c.display_with_short_relation())

        self.assertEqual(result, '\n'.join([
            f'1. {self.parent1.display_with_short_relation()}',
            f'2. {self.parent2.display_with_short_relation()}',
            f'    2.1 {self.child.display_with_short_relation()}',
        ]))

    def test_get_all_scoring_score_criteria_as_numbered_str_uses_model_defaults(self):
        result = self.admission_criteria.get_all_scoring_score_criteria_as_numbered_str()

        self.assertEqual(result, '\n'.join([
            f'1. {self.parent1}',
            f'2. {self.parent2}',
            f'    2.1 {self.child}',
        ]))


class AdditionalFolioCriteriaTestCase(SimpleTestCase):
    """apply_additional_folio_criteria appends export-config text to the
    folio_criteria column of the conditions CSV. Entries are keyed like
    custom_comments ("<program+major>-<project id>"), plus a '*' key that
    applies to every row. Rows with an empty or absent folio_criteria are left
    alone - that covers non-portfolio rows and, crucially, scoring rows, which
    have no such column at all."""

    def make_row(self, program_id='10020104212301A', major_id='',
                 project_id='C2800', folio_criteria='1. GPAX 60%'):
        row = {
            'program_id': program_id,
            'major_id': major_id,
            'project_id': project_id,
        }
        if folio_criteria is not None:
            row['folio_criteria'] = folio_criteria
        return row

    def apply(self, config, rows):
        from criteria.views.cuptexport import apply_additional_folio_criteria

        apply_additional_folio_criteria({'additional_folio_criteria': config}, rows)
        return rows

    def test_appends_matching_entry_on_its_own_line(self):
        row = self.make_row()

        self.apply({'10020104212301A-C2800': 'ส่งใบรับรองแพทย์'}, [row])

        self.assertEqual(row['folio_criteria'], '1. GPAX 60%\nส่งใบรับรองแพทย์')

    def test_star_key_applies_to_every_row(self):
        rows = [self.make_row(project_id='C2800'),
                self.make_row(program_id='10020105303201A', project_id='C2805')]

        self.apply({'*': 'ดูรายละเอียดที่ https://admission.ku.ac.th'}, rows)

        for row in rows:
            self.assertEqual(row['folio_criteria'],
                             '1. GPAX 60%\nดูรายละเอียดที่ https://admission.ku.ac.th')

    def test_matching_entry_comes_before_star_text(self):
        row = self.make_row()

        self.apply({'10020104212301A-C2800': 'เฉพาะสาขานี้',
                    '*': 'ทุกสาขา'}, [row])

        self.assertEqual(row['folio_criteria'], '1. GPAX 60%\nเฉพาะสาขานี้\nทุกสาขา')

    def test_row_keyed_by_program_and_major_code(self):
        # A row with a major_id is keyed by program_id + '0' + major_id.
        row = self.make_row(program_id='10020105303201A', major_id='10')

        self.apply({'10020105303201A010-C2800': 'เฉพาะสาขาย่อย'}, [row])

        self.assertEqual(row['folio_criteria'], '1. GPAX 60%\nเฉพาะสาขาย่อย')

    def test_non_matching_entry_leaves_row_unchanged(self):
        row = self.make_row()

        self.apply({'99999999999999A-C2800': 'ไม่ตรง'}, [row])

        self.assertEqual(row['folio_criteria'], '1. GPAX 60%')

    def test_empty_folio_criteria_is_not_given_the_star_text(self):
        # Non-portfolio rows keep the '' that extract_portfolio_information
        # sets, even when a GLOBAL '*' entry is configured.
        row = self.make_row(folio_criteria='')

        self.apply({'*': 'ทุกสาขา'}, [row])

        self.assertEqual(row['folio_criteria'], '')

    def test_row_without_folio_criteria_does_not_gain_the_column(self):
        # Scoring rows never carry folio_criteria, and the scoring CSV has no
        # such field - adding one would make csv.DictWriter raise.
        row = self.make_row(folio_criteria=None)

        self.apply({'*': 'ทุกสาขา'}, [row])

        self.assertNotIn('folio_criteria', row)


class CriteriaReportIndexTestCase(TestCase):
    """The criteria report landing page (/backoffice/criteria/report/) links
    the two cross-project additional-fields reports and shows per-project
    criteria counts. It lists projects that are available OR visible in the
    backoffice - the same set the CUPT export page uses."""

    def setUp(self):
        self.campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering',
                                              campus=self.campus)
        self.admission_round = AdmissionRound.objects.create(
            number=1, rank=1, acceptance_result_date=datetime.date(2026, 1, 1))

        self.project = AdmissionProject.objects.create(
            title='Visible Project', short_title='Visible',
            is_visible_in_backoffice=True)
        self.project.admission_rounds.add(self.admission_round)

        # Two criteria: one storing form fields, one storing nothing. The
        # deleted one must not be counted at all.
        AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1,
            additional_admission_form_fields_json='[{"title": "q", "size": "short"}]')
        AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1,
            additional_admission_form_fields_json='[]')
        AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1,
            is_deleted=True,
            additional_admission_form_fields_json='[{"title": "gone", "size": "short"}]')

        cupt_code = MajorCuptCode.objects.create(
            program_code='10020104212301', program_type='ปกติ',
            program_type_code='A', faculty=self.faculty, title='Major')
        CurriculumMajor.objects.create(admission_project=self.project,
                                       cupt_code=cupt_code,
                                       faculty=self.faculty)

        self.url = reverse('backoffice:criteria:report-index')

    def _user(self, username, is_admission_admin=False):
        # A Profile is auto-created by a post_save signal on User.
        user = User.objects.create_user(username=username, password='x')
        user.profile.is_admission_admin = is_admission_admin
        user.profile.save()
        return user

    def _stats_for(self, response, project):
        for stat in response.context['project_stats']:
            if stat['project'].id == project.id:
                return stat
        return None

    def test_non_admission_admin_is_redirected(self):
        self.client.force_login(self._user('staff01'))

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('backoffice:index'),
                             fetch_redirect_response=False)

    def test_page_links_both_additional_fields_reports(self):
        self.client.force_login(self._user('admin01', is_admission_admin=True))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, reverse('backoffice:criteria:report-upload-fields'))
        self.assertContains(
            response, reverse('backoffice:criteria:report-form-fields'))

    def test_counts_exclude_deleted_criteria_and_empty_json(self):
        self.client.force_login(self._user('admin01', is_admission_admin=True))

        response = self.client.get(self.url)

        stat = self._stats_for(response, self.project)
        self.assertEqual(stat['criteria_count'], 2)
        self.assertEqual(stat['form_fields_count'], 1)
        self.assertEqual(stat['upload_fields_count'], 0)
        self.assertEqual(stat['major_count'], 1)

    def test_project_with_no_criteria_still_gets_a_zero_row(self):
        empty_project = AdmissionProject.objects.create(
            title='Empty Project', short_title='Empty', is_available=True)
        self.client.force_login(self._user('admin01', is_admission_admin=True))

        response = self.client.get(self.url)

        stat = self._stats_for(response, empty_project)
        self.assertIsNotNone(stat)
        self.assertEqual(stat['criteria_count'], 0)
        self.assertEqual(stat['major_count'], 0)

    def test_project_neither_available_nor_visible_is_not_listed(self):
        hidden_project = AdmissionProject.objects.create(
            title='Old Project', short_title='Old')
        self.client.force_login(self._user('admin01', is_admission_admin=True))

        response = self.client.get(self.url)

        self.assertIsNone(self._stats_for(response, hidden_project))


class MultipleCriteriaMajorsReportTestCase(TestCase):
    """The สาขาที่มีมากกว่า 1 เกณฑ์ report lists every CurriculumMajor holding
    more than one *non-deleted* AdmissionCriteria - the CUPT export's "Too many
    rows" condition. Deleted criteria must not count towards the threshold,
    which is what the filtered Count in the annotation is for."""

    def setUp(self):
        self.campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering',
                                              campus=self.campus)
        self.admission_round = AdmissionRound.objects.create(
            number=1, rank=1, acceptance_result_date=datetime.date(2026, 1, 1))
        self.project = AdmissionProject.objects.create(
            title='Visible Project', short_title='Visible',
            is_visible_in_backoffice=True)
        self.project.admission_rounds.add(self.admission_round)

        self.url = reverse('backoffice:criteria:report-multiple-criteria-majors')
        self.code_counter = 0

    def _curriculum_major(self, project=None):
        self.code_counter += 1
        cupt_code = MajorCuptCode.objects.create(
            program_code='1002010421230%d' % self.code_counter,
            program_type='ปกติ', program_type_code='A',
            faculty=self.faculty, title='Major %d' % self.code_counter)
        return CurriculumMajor.objects.create(
            admission_project=project or self.project,
            cupt_code=cupt_code, faculty=self.faculty)

    def _attach_criteria(self, curriculum_major, count, is_deleted=False):
        for _ in range(count):
            admission_criteria = AdmissionCriteria.objects.create(
                admission_project=curriculum_major.admission_project,
                faculty=self.faculty, version=1, is_deleted=is_deleted)
            CurriculumMajorAdmissionCriteria.objects.create(
                curriculum_major=curriculum_major,
                admission_criteria=admission_criteria, slots=10)

    def _admin(self):
        # A Profile is auto-created by a post_save signal on User.
        user = User.objects.create_user(username='admin01', password='x')
        user.profile.is_admission_admin = True
        user.profile.save()
        return user

    def _majors_in(self, response):
        return [row['curriculum_major'].id for row in response.context['rows']]

    def test_non_admission_admin_is_redirected(self):
        user = User.objects.create_user(username='staff01', password='x')
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertRedirects(response, reverse('backoffice:index'),
                             fetch_redirect_response=False)

    def test_major_with_two_criteria_is_listed_with_both(self):
        curriculum_major = self._curriculum_major()
        self._attach_criteria(curriculum_major, 2)
        self.client.force_login(self._admin())

        response = self.client.get(self.url)

        self.assertEqual(self._majors_in(response), [curriculum_major.id])
        row = response.context['rows'][0]
        self.assertEqual(row['criteria_count'], 2)
        self.assertEqual(len(row['criterias']), 2)

    def test_major_with_one_criteria_is_not_listed(self):
        curriculum_major = self._curriculum_major()
        self._attach_criteria(curriculum_major, 1)
        self.client.force_login(self._admin())

        response = self.client.get(self.url)

        self.assertNotIn(curriculum_major.id, self._majors_in(response))

    def test_deleted_criteria_do_not_count_towards_the_threshold(self):
        # One live criteria plus one deleted is not "more than one".
        curriculum_major = self._curriculum_major()
        self._attach_criteria(curriculum_major, 1)
        self._attach_criteria(curriculum_major, 1, is_deleted=True)
        self.client.force_login(self._admin())

        response = self.client.get(self.url)

        self.assertNotIn(curriculum_major.id, self._majors_in(response))

    def test_deleted_criteria_are_not_shown_for_a_listed_major(self):
        curriculum_major = self._curriculum_major()
        self._attach_criteria(curriculum_major, 2)
        self._attach_criteria(curriculum_major, 1, is_deleted=True)
        self.client.force_login(self._admin())

        response = self.client.get(self.url)

        row = response.context['rows'][0]
        self.assertEqual(row['criteria_count'], 2)
        self.assertEqual(len(row['criterias']), 2)

    def test_major_of_a_project_neither_available_nor_visible_is_not_listed(self):
        hidden_project = AdmissionProject.objects.create(
            title='Old Project', short_title='Old')
        curriculum_major = self._curriculum_major(project=hidden_project)
        self._attach_criteria(curriculum_major, 2)
        self.client.force_login(self._admin())

        response = self.client.get(self.url)

        self.assertNotIn(curriculum_major.id, self._majors_in(response))

    def test_report_index_links_this_report(self):
        self.client.force_login(self._admin())

        response = self.client.get(reverse('backoffice:criteria:report-index'))

        self.assertContains(response, self.url)


class ZeroScoreFieldsExportTestCase(TestCase):
    """is_cupt_export_zero_score_fields sits half way between
    is_cupt_export_only_major_list True and False: rows stay per-criteria (NOT
    combined per major, and add_limit is not forced to 0), but min scores and
    scoring weights are all exported as 0. Only the portfolio/interview split
    still carries a value.

    The two flags are read through uses_grouped_major_rows / zeroes_score_fields,
    which is what keeps those two concerns separable."""

    def setUp(self):
        self.campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering',
                                              campus=self.campus)
        self.cupt_code = MajorCuptCode.objects.create(
            program_code='10020104212301', program_type='ปกติ',
            program_type_code='A', faculty=self.faculty, title='Major')

    def _project(self, **flags):
        project = AdmissionProject.objects.create(
            title='P', short_title='P', cupt_code='A0100',
            is_visible_in_backoffice=True, **flags)
        self.curriculum_major = CurriculumMajor.objects.create(
            admission_project=project, cupt_code=self.cupt_code,
            faculty=self.faculty)
        return project

    def _criteria(self, project, gpax_min='3.00', tgat_weight='30.00'):
        # NOTE: gpax_min must be integral. normalize_int_value returns None for
        # a non-integral value (see docs/criteria-export.md), so a 2.50 minimum
        # would be written as an empty cell and this fixture would be testing
        # that bug rather than the flag.
        """One criteria with a required minimum and a scoring weight, attached
        to the project's single curriculum major."""
        admission_criteria = AdmissionCriteria.objects.create(
            admission_project=project, faculty=self.faculty, version=1)
        ScoreCriteria.objects.create(
            admission_criteria=admission_criteria,
            primary_order=1, secondary_order=0,
            criteria_type='required', score_type='GPAX',
            value=Decimal(gpax_min), description='GPAX')
        ScoreCriteria.objects.create(
            admission_criteria=admission_criteria,
            primary_order=1, secondary_order=0,
            criteria_type='scoring', score_type='TGAT',
            value=Decimal(tgat_weight), description='TGAT')
        CurriculumMajorAdmissionCriteria.objects.create(
            curriculum_major=self.curriculum_major,
            admission_criteria=admission_criteria, slots=10)
        return admission_criteria

    def _condition_rows(self, project):
        from criteria.views.cuptexport import (load_all_criterias,
                                               extract_condition_rows)
        criterias = load_all_criterias()[project.id]
        rows, _ = extract_condition_rows(project, criterias)
        return rows

    def _scoring_rows(self, project):
        from criteria.views.cuptexport import (load_all_criterias,
                                               extract_scoring_rows)
        criterias = load_all_criterias()[project.id]
        rows, _ = extract_scoring_rows(project, criterias)
        return rows

    # --- predicates ---------------------------------------------------

    def test_predicates_separate_the_two_concerns(self):
        from criteria.views.cuptexport import (uses_grouped_major_rows,
                                               zeroes_score_fields)

        grouped = self._project(is_cupt_export_only_major_list=True)
        zeroed = self._project(is_cupt_export_only_major_list=False,
                               is_cupt_export_zero_score_fields=True)
        plain = self._project(is_cupt_export_only_major_list=False)

        self.assertEqual(
            [uses_grouped_major_rows(p) for p in [grouped, zeroed, plain]],
            [True, False, False])
        self.assertEqual(
            [zeroes_score_fields(p) for p in [grouped, zeroed, plain]],
            [True, True, False])

    # --- conditions CSV -----------------------------------------------

    def test_min_scores_are_not_written(self):
        project = self._project(is_cupt_export_only_major_list=False,
                                is_cupt_export_zero_score_fields=True)
        self._criteria(project)

        row = self._condition_rows(project)[0]

        self.assertNotIn('min_gpax', row)
        self.assertNotIn('score_condition', row)

    def test_min_scores_are_written_without_the_flag(self):
        project = self._project(is_cupt_export_only_major_list=False)
        self._criteria(project)

        row = self._condition_rows(project)[0]

        self.assertEqual(row['min_gpax'], 3)

    def test_rows_are_not_combined_per_major(self):
        # The whole point of the new flag: two criteria on one major stay two
        # rows, where only_major_list would have merged them into one.
        project = self._project(is_cupt_export_only_major_list=False,
                                is_cupt_export_zero_score_fields=True)
        self._criteria(project)
        self._criteria(project)

        self.assertEqual(len(self._condition_rows(project)), 2)

    def test_only_major_list_still_combines_rows(self):
        project = self._project(is_cupt_export_only_major_list=True)
        self._criteria(project)
        self._criteria(project)

        rows = self._condition_rows(project)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['slots'], 20)

    def test_add_limit_is_not_forced_to_zero(self):
        project = self._project(is_cupt_export_only_major_list=False,
                                is_cupt_export_zero_score_fields=True)
        self._criteria(project)

        row = self._condition_rows(project)[0]

        self.assertEqual(row['add_limit'],
                         CurriculumMajorAdmissionCriteria.DEFAULT_ADD_LIMIT)

    def test_folio_criteria_still_rendered(self):
        # Score extraction still runs, so the portfolio columns are available.
        project = self._project(is_cupt_export_only_major_list=False,
                                is_cupt_export_zero_score_fields=True)
        self._criteria(project)

        row = self._condition_rows(project)[0]

        self.assertIn('folio_criteria', row)

    # --- scoring CSV ---------------------------------------------------

    def test_scoring_weights_are_not_written(self):
        project = self._project(is_cupt_export_only_major_list=False,
                                is_cupt_export_zero_score_fields=True)
        self._criteria(project)

        row = self._scoring_rows(project)[0]

        self.assertNotIn('tgat', row)
        # cal_* are not in the scoring zero-field list, so they must stay
        # explicitly 0 rather than be left out (an absent key is written as an
        # empty cell, not a zero).
        self.assertEqual(row['cal_type'], 0)
        self.assertEqual(row['cal_score_sum'], 0)
        self.assertEqual(row['cal_subject_name'], 0)

    def test_scoring_weights_are_written_without_the_flag(self):
        project = self._project(is_cupt_export_only_major_list=False)
        self._criteria(project)

        row = self._scoring_rows(project)[0]

        self.assertEqual(row['tgat'], 30)

    def test_portfolio_and_interview_percents_survive(self):
        from criteria.views.cuptexport import (
            load_all_criterias, extract_scoring_rows,
            preprocess_portfolio_admission_criteria)

        project = self._project(is_cupt_export_only_major_list=False,
                                is_cupt_export_zero_score_fields=True)
        self._criteria(project)

        criterias = load_all_criterias()[project.id]
        # What export_scoring_csv does for a portfolio project: replaces the
        # extracted scoring criteria with the R1_PORTFOLIO / R1_INTERVIEW pair.
        preprocess_portfolio_admission_criteria(project, criterias)
        rows, _ = extract_scoring_rows(project, criterias)

        self.assertEqual(rows[0]['portfolio'], 100)
        self.assertEqual(rows[0]['interview'], 0)
        self.assertNotIn('tgat', rows[0])


class NormalizeMinValueTestCase(SimpleTestCase):
    """normalize_int_value returns None for a non-integral value, which the CSV
    writes as an empty cell - so a GPAX minimum of 2.75 used to vanish.
    normalize_min_value exempts the columns that carry real decimals (any field
    name containing 'gpa' or 'tscore') and is used by the conditions export
    only: scoring weights still normalize unconditionally, so an integral gpax
    weight keeps exporting as 20 rather than 20.0."""

    def test_non_integral_value_survives_on_a_gpa_field(self):
        from criteria.views.cuptexport import normalize_min_value

        self.assertEqual(normalize_min_value('min_gpax', 2.75), 2.75)
        self.assertEqual(normalize_min_value('min_credit_gpa22', 2.5), 2.5)

    def test_non_integral_value_survives_on_a_tscore_field(self):
        from criteria.views.cuptexport import normalize_min_value

        self.assertEqual(normalize_min_value('min_tgat_tscore', 33.5), 33.5)

    def test_integral_value_on_a_gpa_field_is_left_as_is(self):
        # Deliberate: 3.00 exports as "3.0", not "3". Keeping the raw value is
        # what makes the non-integral case work.
        from criteria.views.cuptexport import normalize_min_value

        self.assertEqual(normalize_min_value('min_gpax', 3.0), 3.0)
        self.assertIsInstance(normalize_min_value('min_gpax', 3.0), float)

    def test_other_fields_still_normalize_to_int(self):
        from criteria.views.cuptexport import normalize_min_value

        self.assertEqual(normalize_min_value('min_tgat', 30.0), 30)
        self.assertIsInstance(normalize_min_value('min_tgat', 30.0), int)

    def test_other_fields_keep_the_old_none_behaviour(self):
        # Unchanged on purpose - only gpa/tscore columns were in scope.
        from criteria.views.cuptexport import normalize_min_value

        self.assertIsNone(normalize_min_value('min_ielts', 3.5))


class ConditionRowMinValueTestCase(TestCase):
    """The conditions export writes decimal minimums through
    normalize_min_value, including inside an OR group - where a dropped value
    was not merely blank but the literal string "None" in the space-joined
    score_minimum."""

    def setUp(self):
        self.campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering',
                                              campus=self.campus)
        self.cupt_code = MajorCuptCode.objects.create(
            program_code='10020104212301', program_type='ปกติ',
            program_type_code='A', faculty=self.faculty, title='Major')
        self.project = AdmissionProject.objects.create(
            title='P', short_title='P', cupt_code='A0100',
            is_visible_in_backoffice=True,
            is_cupt_export_only_major_list=False)
        self.curriculum_major = CurriculumMajor.objects.create(
            admission_project=self.project, cupt_code=self.cupt_code,
            faculty=self.faculty)
        self.admission_criteria = AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1)
        CurriculumMajorAdmissionCriteria.objects.create(
            curriculum_major=self.curriculum_major,
            admission_criteria=self.admission_criteria, slots=10)

    def _required(self, score_type, value, description, **kwargs):
        return ScoreCriteria.objects.create(
            admission_criteria=self.admission_criteria,
            primary_order=kwargs.pop('primary_order', 1),
            secondary_order=kwargs.pop('secondary_order', 0),
            criteria_type='required', score_type=score_type,
            value=Decimal(value), description=description, **kwargs)

    def _row(self):
        from criteria.views.cuptexport import (load_all_criterias,
                                               extract_condition_rows)
        criterias = load_all_criterias()[self.project.id]
        rows, _ = extract_condition_rows(self.project, criterias)
        return rows[0]

    def test_decimal_gpax_minimum_is_exported(self):
        self._required('GPAX', '2.75', 'GPAX')

        self.assertEqual(self._row()['min_gpax'], 2.75)

    def test_decimal_minimum_in_an_or_group_is_not_the_string_none(self):
        group = self._required('GROUP-OR', '0.00', 'ข้อใดข้อหนึ่ง',
                               relation='OR')
        self._required('GPAX', '2.75', 'GPAX',
                       secondary_order=1, parent=group)
        self._required('TGAT', '30.00', 'TGAT',
                       secondary_order=2, parent=group)

        row = self._row()

        self.assertEqual(row['score_condition'], 1)
        self.assertEqual(row['subject_names'], 'min_gpax min_tgat')
        self.assertEqual(row['score_minimum'], '2.75 30')
        self.assertNotIn('None', row['score_minimum'])
