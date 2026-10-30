import os
import shutil
import tempfile
from datetime import datetime, timedelta

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings

from appl.models import (AdmissionProject, AdmissionProjectRound, AdmissionRound, Campus, Faculty, Major,
                         MajorSelection, ProjectUploadedDocument, UploadedDocument)
from maintenance.document_url_replacement import (
    is_same_link, link_id, ALREADY_DONE, ERROR_INVALID_URL, ERROR_MULTIPLE_DOCUMENTS, ERROR_NO_APPLICANT,
    ERROR_NO_DOCUMENT, ERROR_NOT_IN_MAJOR, REPLACED, TO_REPLACE, URL_MISMATCH,
    URL_REPLACED, URL_TO_REPLACE,
    SetupError, replace_files_with_urls)
from regis.models import Applicant, LogItem

FILE = ProjectUploadedDocument.DOCUMENT_TYPE_FILE
ANY = ProjectUploadedDocument.DOCUMENT_TYPE_ANY

FOLIO_URL = 'https://folio.mytcas.com/view-folio/abc123'
OTHER_FOLIO_URL = 'https://folio.mytcas.com/view-folio/zzz999'


class ReplaceFilesWithUrlsTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        shutil.rmtree(cls.media_root, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.admission_round = AdmissionRound.objects.create(
            number=1, rank=1, is_available=True,
            acceptance_result_date=datetime.now().date())
        self.project = AdmissionProject.objects.create(title='Test Project', short_title='Test')
        AdmissionProjectRound.objects.create(
            admission_project=self.project, admission_round=self.admission_round,
            is_started=True, applying_deadline=datetime.now() + timedelta(days=7),
            payment_deadline=(datetime.now() + timedelta(days=10)).date())
        campus = Campus.objects.create(title='บางเขน', short_title='บางเขน')
        faculty = Faculty.objects.create(title='วิศวกรรมศาสตร์', campus=campus)
        for number in (1, 2):
            Major.objects.create(number=number, title=f'สาขา {number}', faculty=faculty,
                                 admission_project=self.project, slots=10)
        self.slot = self.make_slot(ANY, validator='tcasfolio')
        self.applicant = self.make_applicant('1234567890121', majors='1')

    def make_slot(self, document_type, validator='', major_numbers='', document_key='',
                  is_common_document=False):
        slot = ProjectUploadedDocument.objects.create(
            rank=1, title='Portfolio', descriptions='', specifications='PDF',
            allowed_extentions='PDF', document_type=document_type,
            validator=validator, major_numbers=major_numbers,
            document_key=document_key, is_common_document=is_common_document)
        slot.admission_projects.add(self.project)
        return slot

    def make_applicant(self, national_id, majors):
        applicant = Applicant.objects.create(
            national_id=national_id, prefix='นาย', first_name='ทดสอบ',
            last_name=national_id[-3:], email=f'{national_id}@test.com')
        applicant.apply_to_project(self.project, self.admission_round)
        application = applicant.get_active_application(self.admission_round)
        MajorSelection.objects.create(applicant=applicant, project_application=application,
                                      admission_project=self.project,
                                      admission_round=self.admission_round,
                                      major_list=majors)
        return applicant

    def add_file(self, applicant=None, slot=None):
        document = UploadedDocument(applicant=applicant or self.applicant,
                                    project_uploaded_document=slot or self.slot,
                                    rank=0, original_filename='portfolio.pdf')
        document.uploaded_file.save('portfolio.pdf', ContentFile(b'%PDF-1.4 x'))
        return document

    def add_url(self, url, applicant=None):
        return UploadedDocument.objects.create(applicant=applicant or self.applicant,
                                               project_uploaded_document=self.slot,
                                               rank=0, document_url=url)

    def run_updates(self, updates, major=1, apply=True, document_key=None,
                    replace_mismatch=False):
        return replace_files_with_urls(self.project, major, updates,
                                       document_key=document_key, apply=apply,
                                       replace_mismatch=replace_mismatch)

    def run_one(self, url=FOLIO_URL, national_id='1234567890121', **kwargs):
        _, results = self.run_updates([(national_id, url)], **kwargs)
        return results[0]

    # --- the replacement ---------------------------------------------------

    def test_file_is_replaced_by_url_and_kept(self):
        document = self.add_file()
        old_name = document.uploaded_file.name
        document.local_document_url = 'http://mirror/old.pdf'
        document.save()

        result = self.run_one(url=f'  {FOLIO_URL} ')

        self.assertEqual(result.status, REPLACED)
        self.assertEqual(result.old_file, old_name)
        document.refresh_from_db()
        self.assertTrue(document.is_url())
        self.assertEqual(document.document_url, FOLIO_URL)
        self.assertEqual(document.local_document_url, '')
        self.assertEqual(document.replaced_uploaded_file.name, old_name)
        self.assertEqual(document.original_filename, 'portfolio.pdf')
        self.assertTrue(os.path.exists(document.replaced_uploaded_file.path))
        self.assertTrue(LogItem.objects.filter(
            applicant=self.applicant,
            message__startswith=f'Replaced file of document id {document.id}').exists())

    def test_dry_run_writes_nothing(self):
        document = self.add_file()

        result = self.run_one(apply=False)

        self.assertEqual(result.status, TO_REPLACE)
        document.refresh_from_db()
        self.assertTrue(document.is_file())
        self.assertEqual(document.document_url, '')
        self.assertFalse(LogItem.objects.exists())

    def test_second_run_is_already_done(self):
        self.add_file()
        self.assertEqual(self.run_one().status, REPLACED)
        self.assertEqual(self.run_one().status, ALREADY_DONE)

    # --- documents that are already links ----------------------------------

    def test_same_existing_url_is_already_done(self):
        self.add_url(FOLIO_URL + ' ')
        self.assertEqual(self.run_one().status, ALREADY_DONE)

    def test_existing_url_matches_on_the_id_whatever_the_host(self):
        for current in ('https://student.mytcas.com/view-folio/abc123',
                        'https://folio.mytcas.com/_/abc123',
                        'https://folio.mytcas.com/view-folio/abc123/?x=1#top'):
            UploadedDocument.objects.all().delete()
            self.add_url(current)
            self.assertEqual(self.run_one().status, ALREADY_DONE, current)

    def test_different_existing_url_is_a_warning_and_not_changed(self):
        document = self.add_url(OTHER_FOLIO_URL)

        result = self.run_one()

        self.assertEqual(result.status, URL_MISMATCH)
        self.assertTrue(result.is_warning)
        self.assertEqual(result.current_url, OTHER_FOLIO_URL)
        document.refresh_from_db()
        self.assertEqual(document.document_url, OTHER_FOLIO_URL)

    def test_link_id(self):
        self.assertEqual(link_id(' https://folio.mytcas.com/view-folio/abc123/ '), 'abc123')
        self.assertEqual(link_id('https://folio.mytcas.com/_/abc_19a?x=1'), 'abc_19a')
        self.assertEqual(link_id('https://example.com'), '')

    def test_links_without_an_id_compare_whole(self):
        self.assertTrue(is_same_link(self.slot, 'https://example.com ', 'https://example.com'))
        self.assertFalse(is_same_link(self.slot, 'https://example.com', 'https://example.org'))
        self.assertFalse(is_same_link(self.slot, 'https://example.com', FOLIO_URL))

    def test_other_slots_compare_whole_urls(self):
        plain = ProjectUploadedDocument(document_type=ANY, validator='')
        self.assertTrue(is_same_link(plain, ' https://example.com/a/x1', 'https://example.com/a/x1'))
        self.assertFalse(is_same_link(plain, 'https://example.com/a/x1', 'https://example.org/b/x1'))
        self.assertFalse(is_same_link(plain, 'https://student.mytcas.com/view-folio/abc123',
                                      FOLIO_URL))

    def test_existing_url_in_a_plain_slot_needs_the_whole_url(self):
        self.slot.validator = ''
        self.slot.save()
        self.add_url('https://student.mytcas.com/view-folio/abc123')
        self.assertEqual(self.run_one().status, URL_MISMATCH)

    # --- --replace-mismatch -----------------------------------------------

    def test_replace_mismatch_replaces_the_link_and_logs_the_old_one(self):
        document = self.add_url(OTHER_FOLIO_URL)
        document.replaced_uploaded_file = 'documents/applicant_1/doc_1/old.pdf'
        document.local_document_url = 'http://mirror/old.pdf'
        document.save()

        result = self.run_one(replace_mismatch=True)

        self.assertEqual(result.status, URL_REPLACED)
        self.assertEqual(result.current_url, OTHER_FOLIO_URL)
        document.refresh_from_db()
        self.assertEqual(document.document_url, FOLIO_URL)
        self.assertEqual(document.local_document_url, '')
        self.assertEqual(document.replaced_uploaded_file.name,
                         'documents/applicant_1/doc_1/old.pdf')
        log = LogItem.objects.get(applicant=self.applicant)
        self.assertEqual(log.message,
                         f'Replaced url of document id {document.id} ({self.slot.id}) '
                         f'by script; old: {OTHER_FOLIO_URL}')

    def test_replace_mismatch_log_is_cut_to_the_message_length(self):
        long_url = 'https://folio.mytcas.com/view-folio/' + 'x' * 160
        self.add_url(long_url)
        self.run_one(replace_mismatch=True)
        log = LogItem.objects.get(applicant=self.applicant)
        self.assertEqual(len(log.message), LogItem._meta.get_field('message').max_length)

    def test_replace_mismatch_dry_run_writes_nothing(self):
        document = self.add_url(OTHER_FOLIO_URL)

        result = self.run_one(replace_mismatch=True, apply=False)

        self.assertEqual(result.status, URL_TO_REPLACE)
        document.refresh_from_db()
        self.assertEqual(document.document_url, OTHER_FOLIO_URL)
        self.assertFalse(LogItem.objects.exists())

    def test_replace_mismatch_keeps_same_links_and_still_replaces_files(self):
        self.add_url('https://student.mytcas.com/view-folio/abc123')
        self.assertEqual(self.run_one(replace_mismatch=True).status, ALREADY_DONE)
        UploadedDocument.objects.all().delete()
        self.add_file()
        self.assertEqual(self.run_one(replace_mismatch=True).status, REPLACED)

    def test_replace_mismatch_still_checks_the_new_url(self):
        document = self.add_url(OTHER_FOLIO_URL)
        result = self.run_one(url='https://example.com/x1', replace_mismatch=True)
        self.assertEqual(result.status, ERROR_INVALID_URL)
        document.refresh_from_db()
        self.assertEqual(document.document_url, OTHER_FOLIO_URL)

    # --- refused rows ------------------------------------------------------

    def test_no_or_several_documents(self):
        self.assertEqual(self.run_one().status, ERROR_NO_DOCUMENT)
        self.add_file()
        self.add_file()
        self.assertEqual(self.run_one().status, ERROR_MULTIPLE_DOCUMENTS)

    def test_unknown_applicant(self):
        self.assertEqual(self.run_one(national_id='9999999999999').status, ERROR_NO_APPLICANT)

    def test_applicant_without_the_major_is_refused(self):
        other = self.make_applicant('1234567890122', majors='2')
        self.add_file(applicant=other)
        self.assertEqual(self.run_one(national_id='1234567890122').status, ERROR_NOT_IN_MAJOR)

    def test_canceled_application_is_refused(self):
        self.add_file()
        self.applicant.project_applications.update(is_canceled=True)
        self.assertEqual(self.run_one().status, ERROR_NOT_IN_MAJOR)

    def test_url_must_pass_the_slot_validator(self):
        document = self.add_file()
        for url in ('not-a-url', 'https://example.com/portfolio'):
            result = self.run_one(url=url)
            self.assertEqual(result.status, ERROR_INVALID_URL)
            self.assertTrue(result.is_error)
        document.refresh_from_db()
        self.assertTrue(document.is_file())

    # --- slot and arguments ------------------------------------------------

    def test_unknown_major_is_a_setup_error(self):
        with self.assertRaises(SetupError):
            self.run_updates([], major=9)

    def test_file_only_slots_are_not_candidates(self):
        self.slot.document_type = FILE
        self.slot.save()
        with self.assertRaises(SetupError):
            self.run_updates([])

    def test_several_candidate_slots_need_a_document_key(self):
        second = self.make_slot(ANY, document_key='port-ex')
        with self.assertRaises(SetupError):
            self.run_updates([])
        slot, _ = self.run_updates([], document_key='port-ex')
        self.assertEqual(slot, second)

    def test_document_key_must_match_one_slot_of_the_project(self):
        with self.assertRaises(SetupError):
            self.run_updates([], document_key='no-such-key')
        other_project = AdmissionProject.objects.create(title='Other', short_title='O')
        other = self.make_slot(ANY, document_key='port-ex')
        other.admission_projects.set([other_project])
        with self.assertRaises(SetupError):
            self.run_updates([], document_key='port-ex')

    def test_document_key_can_name_a_common_slot(self):
        common = self.make_slot(ANY, document_key='common-port', is_common_document=True)
        common.admission_projects.clear()
        slot, _ = self.run_updates([], document_key='common-port')
        self.assertEqual(slot, common)

    def test_slot_for_another_major_is_not_a_candidate(self):
        self.make_slot(ANY, major_numbers='2')
        slot, _ = self.run_updates([])
        self.assertEqual(slot, self.slot)

    def test_given_slot_must_be_file_or_link_and_for_the_major(self):
        self.make_slot(FILE, document_key='file-port')
        self.make_slot(ANY, major_numbers='2', document_key='major2-port')
        for key in ('file-port', 'major2-port'):
            with self.assertRaises(SetupError):
                self.run_updates([], document_key=key)

    def test_setup_error_happens_before_any_row(self):
        document = self.add_file()
        self.make_slot(ANY)
        with self.assertRaises(SetupError):
            self.run_updates([('1234567890121', FOLIO_URL)])
        document.refresh_from_db()
        self.assertTrue(document.is_file())
