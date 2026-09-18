import importlib
import json
import logging
import os
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from io import BytesIO
from unittest import mock

from asn1crypto import keys as asn1_keys, x509 as asn1_x509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID, ObjectIdentifier
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from pyhanko.pdf_utils import generic
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.pdf_utils.writer import PageObject, PdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigSeedSubFilter
from pyhanko_certvalidator.registry import SimpleCertificateStore

from appl.document_validators import (DOCUMENT_VALIDATORS, MISCONFIGURED, VERIFICATION_ERROR,
                                      ValidationResult, run_document_validator, tcasfolio)
from appl.models import (AdmissionProject, AdmissionProjectRound, AdmissionRound,
                         MajorSelection, ProjectUploadedDocument, UploadedDocument)
from appl.pdfsignatures import profiles, verify
from appl.views import check_project_documents
from appl.views.upload import get_upload_kind, prepare_deadline_flags, render_validation_message
from regis.models import Applicant

FILE = ProjectUploadedDocument.DOCUMENT_TYPE_FILE
URL = ProjectUploadedDocument.DOCUMENT_TYPE_URL
ANY = ProjectUploadedDocument.DOCUMENT_TYPE_ANY


class DocumentTypeModelTestCase(SimpleTestCase):
    """document_type replaced the old is_url_document boolean; the three
    properties are what the views/templates branch on."""

    def test_document_type_properties(self):
        expected = {
            FILE: (True, False, False),
            URL: (False, True, False),
            ANY: (False, False, True),
        }
        for document_type, (is_file, is_url, is_any) in expected.items():
            doc = ProjectUploadedDocument(document_type=document_type)
            self.assertEqual(doc.is_file_document, is_file)
            self.assertEqual(doc.is_url_document, is_url)
            self.assertEqual(doc.is_any_document, is_any)

    def test_default_document_type_is_file(self):
        self.assertTrue(ProjectUploadedDocument().is_file_document)

    def test_uploaded_document_kind_is_derived(self):
        file_doc = UploadedDocument(uploaded_file='documents/applicant_1/doc_1/a.pdf')
        url_doc = UploadedDocument(document_url='http://example.com/portfolio')
        empty_doc = UploadedDocument()

        self.assertEqual((file_doc.is_file(), file_doc.is_url()), (True, False))
        self.assertEqual((url_doc.is_file(), url_doc.is_url()), (False, True))
        self.assertEqual((empty_doc.is_file(), empty_doc.is_url()), (False, False))

    def test_uploaded_document_with_both_counts_as_file(self):
        # The upload view clears the unused field, but legacy rows might carry
        # both; the file is what can be downloaded, so it wins.
        doc = UploadedDocument(uploaded_file='documents/applicant_1/doc_1/a.pdf',
                               document_url='http://example.com/x')
        self.assertTrue(doc.is_file())
        self.assertFalse(doc.is_url())


class GetUploadKindTestCase(SimpleTestCase):
    """For file/url slots the kind comes from the slot; for 'any' slots it comes
    from what the applicant actually submitted."""

    def setUp(self):
        self.factory = RequestFactory()

    def _request(self, uploaded_file=None, document_url=None):
        data = {}
        if document_url is not None:
            data['document_url'] = document_url
        if uploaded_file is not None:
            data['uploaded_file'] = SimpleUploadedFile('a.pdf', b'%PDF-1.4 x')
        return self.factory.post('/appl/upload/1/', data)

    def test_file_slot_always_file(self):
        doc = ProjectUploadedDocument(document_type=FILE)
        self.assertEqual(get_upload_kind(self._request(uploaded_file=True), doc), 'file')
        self.assertEqual(get_upload_kind(self._request(document_url='http://x.com'), doc), 'file')

    def test_url_slot_always_url(self):
        doc = ProjectUploadedDocument(document_type=URL)
        self.assertEqual(get_upload_kind(self._request(document_url='http://x.com'), doc), 'url')
        self.assertEqual(get_upload_kind(self._request(uploaded_file=True), doc), 'url')

    def test_any_slot_follows_submission(self):
        doc = ProjectUploadedDocument(document_type=ANY)
        self.assertEqual(get_upload_kind(self._request(uploaded_file=True), doc), 'file')
        self.assertEqual(get_upload_kind(self._request(document_url='http://x.com'), doc), 'url')

    def test_any_slot_prefers_file_when_both_submitted(self):
        doc = ProjectUploadedDocument(document_type=ANY)
        request = self._request(uploaded_file=True, document_url='http://x.com')
        self.assertEqual(get_upload_kind(request, doc), 'file')

    def test_any_slot_with_nothing_submitted(self):
        doc = ProjectUploadedDocument(document_type=ANY)
        self.assertIsNone(get_upload_kind(self._request(), doc))
        self.assertIsNone(get_upload_kind(self._request(document_url='   '), doc))


def fake_validator(project_uploaded_document, uploaded_file=None, document_url=None):
    """Rejects files containing b'bad' and urls containing 'bad'."""
    if uploaded_file is not None:
        if b'bad' in uploaded_file.read():
            return ValidationResult.reject('bad_file')
    elif 'bad' in document_url:
        return ValidationResult.reject('bad_url')
    return ValidationResult.accept()


def raising_validator(project_uploaded_document, uploaded_file=None, document_url=None):
    raise RuntimeError('validator bug')


class UploadViewTestCase(TestCase):
    """End-to-end through the AJAX upload endpoint, which is where the
    file-vs-url dispatch and the clearing of the unused field happen."""

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
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test')
        AdmissionProjectRound.objects.create(
            admission_project=self.project,
            admission_round=self.admission_round,
            is_started=True,
            applying_deadline=datetime.now() + timedelta(days=7),
            payment_deadline=(datetime.now() + timedelta(days=10)).date())

        self.applicant = Applicant.objects.create(
            national_id='1234567890121', prefix='นาย',
            first_name='ทดสอบ', last_name='มาก', email='test@test.com')
        self.applicant.apply_to_project(self.project, self.admission_round)

        session = self.client.session
        session['applicant_id'] = self.applicant.id
        session.save()

    def make_document(self, document_type, can_have_multiple_files=False,
                      is_detail_required=False, validator=''):
        doc = ProjectUploadedDocument.objects.create(
            rank=1, title='เอกสาร', descriptions='', specifications='PDF',
            allowed_extentions='PDF', document_type=document_type,
            can_have_multiple_files=can_have_multiple_files,
            is_detail_required=is_detail_required,
            validator=validator)
        doc.admission_projects.add(self.project)
        return doc

    def post_upload(self, doc, **data):
        response = self.client.post(reverse('appl:upload', args=[doc.id]), data)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def post_file(self, doc, filename='portfolio.pdf', content=b'%PDF-1.4 hello', **data):
        return self.post_upload(doc,
                                uploaded_file=SimpleUploadedFile(filename, content),
                                **data)

    def uploaded_documents(self, doc):
        return list(doc.uploaded_document_set.filter(applicant=self.applicant)
                    .order_by('id'))

    # --- 'any' documents ---------------------------------------------------

    def test_any_document_accepts_a_file(self):
        doc = self.make_document(ANY)

        result = self.post_file(doc)

        self.assertEqual(result['result'], 'OK')
        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 1)
        self.assertTrue(uploaded[0].is_file())
        self.assertEqual(uploaded[0].document_url, '')

    def test_any_document_accepts_a_url(self):
        doc = self.make_document(ANY)

        result = self.post_upload(doc, document_url='http://example.com/portfolio')

        self.assertEqual(result['result'], 'OK')
        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 1)
        self.assertTrue(uploaded[0].is_url())
        self.assertEqual(uploaded[0].document_url, 'http://example.com/portfolio')
        self.assertFalse(uploaded[0].uploaded_file)

    def test_any_document_with_both_keeps_only_the_file(self):
        # The mode toggle normally clears the hidden input, but a submission
        # carrying both must still end up unambiguous.
        doc = self.make_document(ANY)

        result = self.post_file(doc, document_url='http://example.com/portfolio')

        self.assertEqual(result['result'], 'OK')
        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 1)
        self.assertTrue(uploaded[0].is_file())
        self.assertEqual(uploaded[0].document_url, '')

    def test_any_document_with_neither_file_nor_url(self):
        doc = self.make_document(ANY)

        result = self.post_upload(doc, detail='ไม่มีอะไร')

        self.assertEqual(result['result'], 'NO_INPUT')
        self.assertEqual(self.uploaded_documents(doc), [])

    def test_any_document_rejects_a_bad_url(self):
        doc = self.make_document(ANY)

        result = self.post_upload(doc, document_url='not-a-url')

        self.assertEqual(result['result'], 'URL_INVALID')
        self.assertEqual(self.uploaded_documents(doc), [])

    def test_any_document_still_checks_file_extension(self):
        doc = self.make_document(ANY)

        result = self.post_file(doc, filename='portfolio.exe')

        self.assertEqual(result['result'], 'EXT_ERROR')
        self.assertEqual(self.uploaded_documents(doc), [])

    def test_any_document_requires_detail_for_both_kinds(self):
        doc = self.make_document(ANY, is_detail_required=True)

        self.assertEqual(self.post_file(doc)['result'], 'DETAIL_REQUIRE')
        self.assertEqual(self.post_upload(doc, document_url='http://example.com/x')['result'],
                         'DETAIL_REQUIRE')
        self.assertEqual(self.uploaded_documents(doc), [])

        self.assertEqual(self.post_file(doc, detail='ไฟล์')['result'], 'OK')
        self.assertEqual(len(self.uploaded_documents(doc)), 1)

    def test_multiple_files_allows_mixing_files_and_urls(self):
        doc = self.make_document(ANY, can_have_multiple_files=True)

        self.post_file(doc, filename='one.pdf')
        self.post_upload(doc, document_url='http://example.com/one')
        self.post_file(doc, filename='two.pdf')
        self.post_upload(doc, document_url='http://example.com/two')

        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 4)
        self.assertEqual([d.is_file() for d in uploaded], [True, False, True, False])

    def test_single_file_document_replaces_across_kinds(self):
        doc = self.make_document(ANY, can_have_multiple_files=False)

        self.post_file(doc)
        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 1)

        # a url submission replaces the file...
        self.post_upload(doc, document_url='http://example.com/portfolio')
        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 1)
        self.assertTrue(uploaded[0].is_url())

        # ...and a file submission replaces the url.
        self.post_file(doc)
        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 1)
        self.assertTrue(uploaded[0].is_file())

    # --- file-only / url-only documents are unchanged ----------------------

    def test_file_document_ignores_a_url(self):
        doc = self.make_document(FILE)

        result = self.post_upload(doc, document_url='http://example.com/portfolio')

        self.assertEqual(result['result'], 'FORM_ERROR')
        self.assertEqual(self.uploaded_documents(doc), [])

    def test_file_document_accepts_a_file(self):
        doc = self.make_document(FILE)

        self.assertEqual(self.post_file(doc)['result'], 'OK')
        self.assertTrue(self.uploaded_documents(doc)[0].is_file())

    def test_url_document_accepts_a_url(self):
        doc = self.make_document(URL)

        result = self.post_upload(doc, document_url='http://example.com/portfolio')

        self.assertEqual(result['result'], 'OK')
        uploaded = self.uploaded_documents(doc)
        self.assertTrue(uploaded[0].is_url())
        self.assertFalse(uploaded[0].uploaded_file)

    def test_url_document_with_both_keeps_only_the_url(self):
        doc = self.make_document(URL)

        result = self.post_file(doc, document_url='http://example.com/portfolio')

        self.assertEqual(result['result'], 'OK')
        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 1)
        self.assertTrue(uploaded[0].is_url())
        self.assertFalse(uploaded[0].uploaded_file)

    def test_url_document_rejects_a_file_only_submission(self):
        doc = self.make_document(URL)

        result = self.post_file(doc)

        self.assertEqual(result['result'], 'URL_INVALID')
        self.assertEqual(self.uploaded_documents(doc), [])

    # --- custom validators -------------------------------------------------

    @mock.patch.dict(DOCUMENT_VALIDATORS, {'fake': fake_validator})
    def test_validator_rejects_a_file_and_keeps_the_old_one(self):
        doc = self.make_document(FILE, validator='fake')
        self.assertEqual(self.post_file(doc, content=b'%PDF-1.4 good')['result'], 'OK')

        result = self.post_file(doc, content=b'%PDF-1.4 bad')

        self.assertEqual(result['result'], 'VALIDATION_ERROR')
        self.assertIn('เอกสารไม่ผ่านการตรวจสอบ', result['message_html'])
        uploaded = self.uploaded_documents(doc)
        self.assertEqual(len(uploaded), 1)
        self.assertEqual(uploaded[0].uploaded_file.read(), b'%PDF-1.4 good')

    @mock.patch.dict(DOCUMENT_VALIDATORS, {'fake': fake_validator})
    def test_validator_accepts_a_file_and_saves_all_of_it(self):
        doc = self.make_document(FILE, validator='fake')

        self.assertEqual(self.post_file(doc, content=b'%PDF-1.4 good')['result'], 'OK')

        self.assertEqual(self.uploaded_documents(doc)[0].uploaded_file.read(), b'%PDF-1.4 good')

    @mock.patch.dict(DOCUMENT_VALIDATORS, {'fake': fake_validator})
    def test_validator_checks_urls(self):
        doc = self.make_document(ANY, validator='fake')

        result = self.post_upload(doc, document_url='http://example.com/bad')
        self.assertEqual(result['result'], 'VALIDATION_ERROR')
        self.assertIn('message_html', result)
        self.assertEqual(self.uploaded_documents(doc), [])

        self.assertEqual(self.post_upload(doc, document_url='http://example.com/good')['result'], 'OK')

    def test_basic_checks_run_before_the_validator(self):
        validator = mock.Mock(return_value=ValidationResult.reject('never'))
        doc = self.make_document(FILE, validator='mocked')

        with mock.patch.dict(DOCUMENT_VALIDATORS, {'mocked': validator}):
            result = self.post_file(doc, filename='portfolio.exe')

        self.assertEqual(result['result'], 'EXT_ERROR')
        self.assertNotIn('message_html', result)
        validator.assert_not_called()

    def test_unknown_validator_rejects_uploads(self):
        doc = self.make_document(FILE, validator='no-such-validator')

        with self.assertLogs('appl.document_validators', level='ERROR'):
            result = self.post_file(doc)

        self.assertEqual(result['result'], 'VALIDATION_ERROR')
        self.assertIn('ติดต่อเจ้าหน้าที่', result['message_html'])
        self.assertEqual(self.uploaded_documents(doc), [])

    def test_tcasfolio_rejects_an_unsigned_pdf(self):
        doc = self.make_document(FILE, validator='tcasfolio')

        result = self.post_file(doc, content=SignedPdfFixtures().unsigned_pdf)

        self.assertEqual(result['result'], 'VALIDATION_ERROR')
        self.assertIn('TCASFolio', result['message_html'])
        self.assertEqual(self.uploaded_documents(doc), [])

    # --- major-specific and late-upload slots ------------------------------

    def select_majors(self, major_list):
        application = self.applicant.get_active_application(self.admission_round)
        MajorSelection.objects.create(
            applicant=self.applicant, project_application=application,
            admission_project=self.project, admission_round=self.admission_round,
            major_list=major_list, num_selected=len(major_list.split(',')))

    def close_applications(self):
        AdmissionProjectRound.objects.filter(admission_project=self.project).update(
            applying_deadline=datetime.now() - timedelta(days=1))

    def post_url_status(self, doc):
        response = self.client.post(reverse('appl:upload', args=[doc.id]),
                                    {'document_url': 'http://example.com/portfolio'})
        return response.status_code

    def test_slot_for_a_selected_major_accepts_uploads(self):
        self.select_majors('1,2')
        doc = self.make_document(URL)
        doc.major_numbers = '2,5'
        doc.save()

        result = self.post_upload(doc, document_url='http://example.com/portfolio')

        self.assertEqual(result['result'], 'OK')

    def test_slot_for_other_majors_is_forbidden(self):
        self.select_majors('1')
        doc = self.make_document(URL)
        doc.major_numbers = '2'
        doc.save()

        self.assertEqual(self.post_url_status(doc), 403)
        self.assertEqual(self.uploaded_documents(doc), [])

    def test_major_specific_slot_is_forbidden_without_a_major_selection(self):
        doc = self.make_document(URL)
        doc.major_numbers = '1'
        doc.save()

        self.assertEqual(self.post_url_status(doc), 403)

    def test_slot_of_another_project_is_forbidden(self):
        doc = self.make_document(URL)
        doc.admission_projects.clear()

        self.assertEqual(self.post_url_status(doc), 403)

    def test_common_document_needs_no_project_link(self):
        doc = self.make_document(URL)
        doc.admission_projects.clear()
        doc.is_common_document = True
        doc.save()

        self.assertEqual(self.post_upload(doc, document_url='http://example.com/x')['result'], 'OK')

    def test_ordinary_slot_is_closed_after_the_deadline(self):
        self.close_applications()
        doc = self.make_document(URL)

        self.assertEqual(self.post_url_status(doc), 403)

    def test_late_upload_slot_stays_open_until_the_late_upload_date(self):
        self.close_applications()
        doc = self.make_document(URL)
        doc.is_late_upload_allowed = True
        doc.save()

        # no late_upload_date: no late upload at all
        self.assertEqual(self.post_url_status(doc), 403)

        self.project.late_upload_date = (datetime.now() + timedelta(days=1)).date()
        self.project.save()
        self.assertEqual(self.post_upload(doc, document_url='http://example.com/x')['result'], 'OK')

        self.project.late_upload_date = (datetime.now() - timedelta(days=1)).date()
        self.project.save()
        self.assertEqual(self.post_url_status(doc), 403)

    def test_delete_from_a_hidden_slot_is_forbidden(self):
        self.select_majors('1')
        doc = self.make_document(URL)
        doc.major_numbers = '1'
        doc.save()
        self.post_upload(doc, document_url='http://example.com/portfolio')
        uploaded = self.uploaded_documents(doc)[0]

        doc.major_numbers = '2'
        doc.save()
        response = self.client.post(reverse('appl:document-delete',
                                            args=[self.applicant.id, doc.id, uploaded.id]))

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.uploaded_documents(doc), [uploaded])


class MajorSpecificDocumentTestCase(SimpleTestCase):
    """ProjectUploadedDocument.major_numbers limits a slot (and its
    requiredness) to applicants who selected one of those majors."""

    def make_document(self, major_numbers='', **kwargs):
        return ProjectUploadedDocument(title='เอกสาร', major_numbers=major_numbers, **kwargs)

    def selection(self, major_list):
        return MajorSelection(major_list=major_list)

    def test_major_numbers_are_parsed_leniently(self):
        self.assertEqual(self.make_document(' 1, 3,,x ,12').get_major_numbers(), [1, 3, 12])
        self.assertEqual(self.make_document('').get_major_numbers(), [])

    def test_blank_major_numbers_are_visible_to_everyone(self):
        doc = self.make_document('')
        self.assertTrue(doc.is_visible_for(None))
        self.assertTrue(doc.is_visible_for(self.selection('4')))

    def test_major_numbers_are_visible_only_for_selected_majors(self):
        doc = self.make_document('2,3')
        self.assertTrue(doc.is_visible_for(self.selection('1,3')))
        self.assertFalse(doc.is_visible_for(self.selection('1,4')))
        self.assertFalse(doc.is_visible_for(None))

    def test_filter_visible(self):
        everyone = self.make_document('')
        major1 = self.make_document('1')
        major2 = self.make_document('2')

        self.assertEqual(ProjectUploadedDocument.filter_visible([everyone, major1, major2],
                                                               self.selection('2')),
                         [everyone, major2])

    def test_late_upload_needs_the_flag_and_a_future_date(self):
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        yesterday = (datetime.now() - timedelta(days=1)).date()
        late = self.make_document(is_late_upload_allowed=True)

        self.assertTrue(late.is_late_upload_open(AdmissionProject(late_upload_date=tomorrow)))
        self.assertTrue(late.is_late_upload_open(AdmissionProject(late_upload_date=datetime.now().date())))
        self.assertFalse(late.is_late_upload_open(AdmissionProject(late_upload_date=yesterday)))
        self.assertFalse(late.is_late_upload_open(AdmissionProject(late_upload_date=None)))
        self.assertFalse(late.is_late_upload_open(None))
        self.assertFalse(self.make_document().is_late_upload_open(
            AdmissionProject(late_upload_date=tomorrow)))

    def test_interview_documents_stay_uploadable_after_the_deadline(self):
        doc = self.make_document(is_interview_document=True)
        self.assertTrue(doc.is_uploadable_after_deadline(AdmissionProject()))
        self.assertFalse(self.make_document().is_uploadable_after_deadline(AdmissionProject()))

    def test_check_project_documents_counts_only_visible_slots(self):
        def slot(title, major_numbers, is_required, requirement_key=''):
            doc = ProjectUploadedDocument(title=title, major_numbers=major_numbers,
                                          is_required=is_required,
                                          requirement_key=requirement_key)
            doc.applicant_uploaded_documents = []
            return doc

        hidden_required = slot('hidden', '2', True)
        visible_required = slot('visible', '1', True)
        or_a = slot('or-a', '', False, 'portfolio')
        or_b = slot('or-b', '1', False, 'portfolio')
        or_b.applicant_uploaded_documents = [UploadedDocument()]

        docs = ProjectUploadedDocument.filter_visible(
            [hidden_required, visible_required, or_a, or_b], self.selection('1'))
        status = check_project_documents(None, AdmissionProject(id=1), [], docs)

        self.assertFalse(status['status'])
        self.assertEqual(status['errors'], ['ยังไม่ได้อัพโหลดvisible'])

        visible_required.applicant_uploaded_documents = [UploadedDocument()]
        self.assertTrue(check_project_documents(None, AdmissionProject(id=1), [], docs)['status'])


class LateUploadCardTemplateTestCase(SimpleTestCase):

    def render(self, doc, admission_project):
        doc.applicant_uploaded_documents = []
        prepare_deadline_flags(doc, admission_project)
        return render_to_string('appl/include/document_upload_form.html',
                                {'project_uploaded_document': doc,
                                 'applicant': Applicant(id=3),
                                 'is_deadline_passed': True,
                                 'toggle': 'show'})

    def make_document(self, **kwargs):
        return ProjectUploadedDocument(id=7, rank=1, title='เอกสาร', descriptions='',
                                       specifications='ลิงก์', allowed_extentions='PDF',
                                       document_type=URL, **kwargs)

    def test_open_late_upload_slot_keeps_its_form_and_shows_the_cut_off(self):
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        html = self.render(self.make_document(is_late_upload_allowed=True),
                           AdmissionProject(late_upload_date=tomorrow))

        self.assertIn('name="document_url"', html)
        self.assertIn('อัพโหลดได้ถึงวันที่', html)

    def test_ordinary_slot_has_no_form_after_the_deadline(self):
        tomorrow = (datetime.now() + timedelta(days=1)).date()

        html = self.render(self.make_document(),
                           AdmissionProject(late_upload_date=tomorrow))

        self.assertNotIn('name="document_url"', html)
        self.assertNotIn('อัพโหลดได้ถึงวันที่', html)


class UploadFormTemplateTestCase(SimpleTestCase):
    """The applicant-side card: which inputs show per document_type, and the
    per-row (not per-slot) rendering of already-uploaded entries."""

    def render(self, document_type, uploaded_documents=None,
               can_have_multiple_files=False):
        doc = ProjectUploadedDocument(
            id=7, rank=1, title='เอกสาร', descriptions='', specifications='PDF',
            allowed_extentions='PDF', document_type=document_type,
            can_have_multiple_files=can_have_multiple_files)
        doc.applicant_uploaded_documents = uploaded_documents or []
        return render_to_string('appl/include/document_upload_form.html',
                                {'project_uploaded_document': doc,
                                 'applicant': Applicant(id=3),
                                 'toggle': 'show'})

    def test_file_document_shows_only_a_file_input(self):
        html = self.render(FILE)
        self.assertIn('name="uploaded_file"', html)
        self.assertNotIn('name="document_url"', html)
        self.assertNotIn('upload-mode-radios', html)

    def test_url_document_shows_only_a_url_input(self):
        html = self.render(URL)
        self.assertIn('name="document_url"', html)
        self.assertNotIn('name="uploaded_file"', html)
        self.assertNotIn('upload-mode-radios', html)

    def test_any_document_shows_the_mode_toggle_and_both_inputs(self):
        html = self.render(ANY)
        self.assertIn('upload-mode-radios', html)
        self.assertIn('upload-mode-file-7', html)
        self.assertIn('upload-mode-url-7', html)
        self.assertIn('name="uploaded_file"', html)
        self.assertIn('name="document_url"', html)

    def test_mixed_entries_render_per_row(self):
        file_doc = UploadedDocument(id=1, detail='ไฟล์',
                                    uploaded_file='documents/applicant_3/doc_7/a.pdf')
        url_doc = UploadedDocument(id=2, detail='ลิงก์',
                                   document_url='http://example.com/portfolio')

        html = self.render(ANY, [file_doc, url_doc])

        # the file entry gets a download link, the url entry an external link
        file_link = 'href="%s"' % reverse('appl:document-download', args=[3, 7, 1])
        url_link = 'href="%s"' % reverse('appl:document-download', args=[3, 7, 2])
        self.assertIn(file_link, html)
        self.assertIn('href="http://example.com/portfolio"', html)
        self.assertNotIn(url_link, html)


class ReplaceConfirmTemplateTestCase(SimpleTestCase):
    """Uploading to a single-document slot deletes what is already there, so the
    card carries an inline confirmation panel. It depends only on
    can_have_multiple_files + existing entries, never on document_type."""

    def render(self, document_type, uploaded_documents=None,
               can_have_multiple_files=False):
        return UploadFormTemplateTestCase().render(
            document_type, uploaded_documents, can_have_multiple_files)

    def file_entry(self, id=1, detail='', filename='a.pdf'):
        return UploadedDocument(
            id=id, detail=detail,
            uploaded_file='documents/applicant_3/doc_7/' + filename)

    def url_entry(self, id=2, detail='', url='http://example.com/portfolio'):
        return UploadedDocument(id=id, detail=detail, document_url=url)

    def assertHasConfirm(self, html):
        self.assertIn('data-replace-confirm="true"', html)
        self.assertIn('upload-replace-confirms', html)
        self.assertIn('upload-replace-confirm-buttons', html)
        self.assertIn('upload-replace-cancel-buttons', html)

    def assertHasNoConfirm(self, html):
        self.assertNotIn('data-replace-confirm="true"', html)
        self.assertNotIn('upload-replace-confirms', html)

    def test_no_confirmation_when_nothing_uploaded_yet(self):
        for document_type in [FILE, URL, ANY]:
            with self.subTest(document_type=document_type):
                self.assertHasNoConfirm(self.render(document_type))

    def test_no_confirmation_when_multiple_files_allowed(self):
        # Nothing gets replaced, so there is nothing to confirm.
        for document_type in [FILE, URL, ANY]:
            with self.subTest(document_type=document_type):
                html = self.render(document_type, [self.file_entry()],
                                   can_have_multiple_files=True)
                self.assertHasNoConfirm(html)

    def test_confirmation_for_a_single_file_document(self):
        html = self.render(FILE, [self.file_entry(filename='transcript.pdf')])

        self.assertHasConfirm(html)
        self.assertIn('transcript.pdf', html)

    def test_confirmation_for_a_single_url_document(self):
        html = self.render(URL, [self.url_entry(url='http://example.com/mylink')])

        self.assertHasConfirm(html)
        # No detail, so the link itself names the entry being replaced.
        self.assertIn('http://example.com/mylink', html)

    def test_confirmation_names_a_url_entry_by_its_detail(self):
        html = self.render(URL, [self.url_entry(detail='แฟ้มสะสมผลงาน')])

        self.assertHasConfirm(html)
        self.assertIn('แฟ้มสะสมผลงาน', html)

    def test_confirmation_for_an_any_document_holding_a_file(self):
        html = self.render(ANY, [self.file_entry(filename='portfolio.pdf')])

        self.assertHasConfirm(html)
        self.assertIn('portfolio.pdf', html)

    def test_confirmation_for_an_any_document_holding_a_url(self):
        html = self.render(ANY, [self.url_entry(url='http://example.com/mylink')])

        self.assertHasConfirm(html)
        self.assertIn('http://example.com/mylink', html)


class TrustRootsTestCase(SimpleTestCase):
    """Bundled root certificates must match the fingerprints pinned in
    appl.pdfsignatures.profiles."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def copy_roots(self):
        for filename in os.listdir(profiles.TRUST_ROOTS_DIR):
            shutil.copy(os.path.join(profiles.TRUST_ROOTS_DIR, filename), self.tmpdir)

    def test_every_profile_loads(self):
        for name, profile in profiles.PROFILES.items():
            roots = profiles.load_trust_roots(name)
            self.assertEqual(len(roots), len(profile['roots']))

    def test_tcasfolio_bundles_nrca_g1_and_g3(self):
        filenames = [filename for filename, _ in profiles.TCASFOLIO['roots']]
        self.assertEqual(filenames, ['thailand-nrca-g1.pem', 'thailand-nrca-g3.pem'])
        self.assertEqual(profiles.TCASFOLIO['signer']['organization_identifier'],
                         'TIN-0993000086848')

    def test_swapped_root_file_is_rejected(self):
        self.copy_roots()
        shutil.copy(os.path.join(self.tmpdir, 'thailand-nrca-g3.pem'),
                    os.path.join(self.tmpdir, 'thailand-nrca-g1.pem'))

        with self.assertRaises(profiles.TrustRootError):
            profiles.load_trust_roots('tcasfolio', self.tmpdir)

    def test_edited_root_file_is_rejected(self):
        self.copy_roots()
        path = os.path.join(self.tmpdir, 'thailand-nrca-g1.pem')
        with open(path) as f:
            lines = f.read().split('\n')
        lines[5] = lines[5][:-4] + ('AAAA' if lines[5][-4:] != 'AAAA' else 'BBBB')
        with open(path, 'w') as f:
            f.write('\n'.join(lines))

        with self.assertRaises(profiles.TrustRootError):
            profiles.load_trust_roots('tcasfolio', self.tmpdir)

    def test_file_with_two_certificates_is_rejected(self):
        with open(os.path.join(profiles.TRUST_ROOTS_DIR, 'thailand-nrca-g1.pem'), 'rb') as f:
            pem = f.read()

        with self.assertRaises(profiles.TrustRootError):
            profiles.pem_to_der(pem + pem)

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(profiles.TrustRootError):
            profiles.load_trust_roots('no-such-profile')


class DocumentValidatorRunnerTestCase(SimpleTestCase):

    def make_document(self, validator):
        return ProjectUploadedDocument(id=1, validator=validator)

    def test_blank_validator_accepts(self):
        result = run_document_validator(self.make_document(''),
                                        uploaded_file=SimpleUploadedFile('a.pdf', b'bad'))
        self.assertTrue(result.is_valid)

    @mock.patch.dict(DOCUMENT_VALIDATORS, {'fake': fake_validator})
    def test_dispatches_file_and_url(self):
        doc = self.make_document('fake')

        self.assertTrue(run_document_validator(
            doc, uploaded_file=SimpleUploadedFile('a.pdf', b'good')).is_valid)
        self.assertEqual(run_document_validator(
            doc, uploaded_file=SimpleUploadedFile('a.pdf', b'bad')).code, 'bad_file')
        self.assertTrue(run_document_validator(
            doc, document_url='http://example.com/good').is_valid)
        self.assertEqual(run_document_validator(
            doc, document_url='http://example.com/bad').code, 'bad_url')

    @mock.patch.dict(DOCUMENT_VALIDATORS, {'fake': fake_validator})
    def test_file_is_rewound_after_validation(self):
        uploaded_file = SimpleUploadedFile('a.pdf', b'good content')
        uploaded_file.read(4)

        run_document_validator(self.make_document('fake'), uploaded_file=uploaded_file)

        self.assertEqual(uploaded_file.read(), b'good content')

    def test_unknown_validator_fails_closed(self):
        with self.assertLogs('appl.document_validators', level='ERROR'):
            result = run_document_validator(self.make_document('no-such-validator'),
                                            document_url='http://example.com/')

        self.assertFalse(result.is_valid)
        self.assertEqual(result.code, MISCONFIGURED)

    @mock.patch.dict(DOCUMENT_VALIDATORS, {'raising': raising_validator})
    def test_validator_exception_fails_closed(self):
        with self.assertLogs('appl.document_validators', level='ERROR'):
            result = run_document_validator(self.make_document('raising'),
                                            document_url='http://example.com/')

        self.assertFalse(result.is_valid)
        self.assertEqual(result.code, VERIFICATION_ERROR)


class ValidationMessageTemplateTestCase(SimpleTestCase):

    def render(self, validator, code):
        return render_validation_message(ProjectUploadedDocument(validator=validator),
                                         ValidationResult.reject(code), None)

    def test_every_tcasfolio_code_has_a_specific_message(self):
        for code in [verify.NOT_PDF, verify.NOT_SIGNED, verify.MODIFIED_AFTER_SIGNING,
                     verify.SIGNATURE_INVALID, verify.UNTRUSTED_SIGNER]:
            self.assertIn('TCASFolio', self.render('tcasfolio', code), code)

    def test_tcasfolio_falls_back_to_default_messages(self):
        self.assertIn('ติดต่อเจ้าหน้าที่', self.render('tcasfolio', VERIFICATION_ERROR))

    def test_validator_without_template_uses_default(self):
        self.assertIn('เอกสารไม่ผ่านการตรวจสอบ', self.render('fake', 'bad_file'))
        self.assertIn('ติดต่อเจ้าหน้าที่', self.render('no-such-validator', MISCONFIGURED))


class SignedPdfFixtures:
    """Builds a throwaway root -> intermediate -> signer chain and signs a
    one-page PDF with it, shaped like a TCASFolio file."""

    SIGNER_PIN = {
        'organization_identifier': 'TIN-0000000000000',
        'organization_name': 'Test Signing Organization',
    }

    def __init__(self):
        now = datetime.now(timezone.utc)
        self.now = now

        self.root_key = self.new_key()
        self.root = self.make_cert(self.name('Test Root'), self.root_key,
                                   self.name('Test Root'), self.root_key, is_ca=True)
        self.intermediate_key = self.new_key()
        self.intermediate = self.make_cert(self.name('Test Intermediate'), self.intermediate_key,
                                           self.root.subject, self.root_key, is_ca=True)

        self.unsigned_pdf = self.make_blank_pdf()
        self.signed_pdf = self.sign(self.make_signer_cert())

    @staticmethod
    def new_key():
        return ec.generate_private_key(ec.SECP256R1())

    @staticmethod
    def der(cert):
        return cert.public_bytes(serialization.Encoding.DER)

    @staticmethod
    def name(common_name, organization=None, organization_identifier=None):
        attributes = [x509.NameAttribute(NameOID.COUNTRY_NAME, 'TH')]
        if organization:
            attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization))
        attributes.append(x509.NameAttribute(NameOID.COMMON_NAME, common_name))
        if organization_identifier:
            attributes.append(x509.NameAttribute(ObjectIdentifier('2.5.4.97'),
                                                 organization_identifier))
        return x509.Name(attributes)

    def make_cert(self, subject, key, issuer, issuer_key, is_ca, not_valid_after=None):
        builder = (x509.CertificateBuilder()
                   .subject_name(subject)
                   .issuer_name(issuer)
                   .public_key(key.public_key())
                   .serial_number(x509.random_serial_number())
                   .not_valid_before(self.now - timedelta(days=2))
                   .not_valid_after(not_valid_after or self.now + timedelta(days=365))
                   .add_extension(x509.BasicConstraints(ca=is_ca, path_length=None),
                                  critical=True))
        if is_ca:
            key_usage = x509.KeyUsage(False, False, False, False, False, True, True, False, False)
        else:
            key_usage = x509.KeyUsage(True, True, False, False, False, False, False, False, False)
        return builder.add_extension(key_usage, critical=True).sign(issuer_key, hashes.SHA256())

    def make_signer_cert(self, organization_identifier=None, not_valid_after=None):
        self.signer_key = self.new_key()
        subject = self.name('Test Signer',
                            self.SIGNER_PIN['organization_name'],
                            organization_identifier or self.SIGNER_PIN['organization_identifier'])
        return self.make_cert(subject, self.signer_key,
                              self.intermediate.subject, self.intermediate_key,
                              is_ca=False, not_valid_after=not_valid_after)

    def make_blank_pdf(self):
        writer = PdfFileWriter()
        writer.insert_page(PageObject(contents=[], media_box=generic.ArrayObject(
            [generic.NumberObject(v) for v in (0, 0, 200, 200)])))
        output = BytesIO()
        writer.write(output)
        return output.getvalue()

    def sign(self, signer_cert):
        signer = signers.SimpleSigner(
            signing_cert=asn1_x509.Certificate.load(self.der(signer_cert)),
            signing_key=asn1_keys.PrivateKeyInfo.load(self.signer_key.private_bytes(
                serialization.Encoding.DER, serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption())),
            cert_registry=SimpleCertificateStore.from_certs(
                [asn1_x509.Certificate.load(self.der(self.intermediate))]))
        metadata = signers.PdfSignatureMetadata(
            field_name='Signature1', md_algorithm='sha256',
            subfilter=SigSeedSubFilter.ADOBE_PKCS7_DETACHED)
        output = signers.sign_pdf(IncrementalPdfFileWriter(BytesIO(self.unsigned_pdf)),
                                  metadata, signer=signer)
        return output.getvalue()


class PdfSignatureVerifyTestCase(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # pyHanko logs a traceback for each untrusted path it rejects
        cls.pyhanko_logger = logging.getLogger('pyhanko')
        cls.pyhanko_log_level = cls.pyhanko_logger.level
        cls.pyhanko_logger.setLevel(logging.CRITICAL)
        cls.fixtures = SignedPdfFixtures()

    @classmethod
    def tearDownClass(cls):
        cls.pyhanko_logger.setLevel(cls.pyhanko_log_level)
        super().tearDownClass()

    def check(self, pdf_bytes, roots=None, pin=None):
        f = self.fixtures
        return verify.verify_pdf_signature(pdf_bytes,
                                           roots or [f.der(f.root)],
                                           pin or f.SIGNER_PIN)

    def test_valid_signature(self):
        self.assertEqual(self.check(self.fixtures.signed_pdf), verify.OK)

    def test_not_a_pdf(self):
        self.assertEqual(self.check(b'hello, not a pdf').code, verify.NOT_PDF)

    def test_unsigned_pdf(self):
        self.assertEqual(self.check(self.fixtures.unsigned_pdf).code, verify.NOT_SIGNED)

    def test_bytes_appended_after_signing(self):
        self.assertEqual(self.check(self.fixtures.signed_pdf + b'\n%extra\n').code,
                         verify.MODIFIED_AFTER_SIGNING)

    def test_signed_content_changed(self):
        pdf = self.fixtures.signed_pdf
        # same-length change inside the signed revision's page dictionary
        position = pdf.index(b'200', pdf.index(b'/MediaBox'))
        tampered = pdf[:position] + b'201' + pdf[position + 3:]

        self.assertEqual(self.check(tampered).code, verify.SIGNATURE_INVALID)

    def test_signer_not_matching_pin(self):
        pin = dict(self.fixtures.SIGNER_PIN, organization_identifier='TIN-9999999999999')
        self.assertEqual(self.check(self.fixtures.signed_pdf, pin=pin).code,
                         verify.UNTRUSTED_SIGNER)

    def test_chain_to_an_unbundled_root(self):
        f = self.fixtures
        other_key = f.new_key()
        other_root = f.make_cert(f.name('Other Root'), other_key,
                                 f.name('Other Root'), other_key, is_ca=True)

        self.assertEqual(self.check(f.signed_pdf, roots=[f.der(other_root)]).code,
                         verify.UNTRUSTED_SIGNER)

    def test_expired_signer_certificate(self):
        f = SignedPdfFixtures()
        expired_pdf = f.sign(f.make_signer_cert(not_valid_after=f.now - timedelta(days=1)))

        self.assertEqual(verify.verify_pdf_signature(expired_pdf, [f.der(f.root)], f.SIGNER_PIN).code,
                         verify.UNTRUSTED_SIGNER)


class TcasfolioValidatorTestCase(SimpleTestCase):

    def test_tcasfolio_url_is_accepted(self):
        url = 'https://student.mytcas.com/view-folio/abc123'
        self.assertTrue(tcasfolio.validate(None, document_url=url).is_valid)
        self.assertTrue(tcasfolio.validate(None, document_url='  ' + url + '  ').is_valid)

    def test_other_url_is_rejected(self):
        result = tcasfolio.validate(None, document_url='http://example.com/any')

        self.assertFalse(result.is_valid)
        self.assertEqual(result.code, 'invalid_url')

    def test_missing_url_is_rejected(self):
        result = tcasfolio.validate(None)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.code, 'no_document')

    def test_unsigned_file_is_rejected(self):
        result = tcasfolio.validate(None, uploaded_file=SimpleUploadedFile(
            'portfolio.pdf', SignedPdfFixtures().unsigned_pdf))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.code, verify.NOT_SIGNED)

    @unittest.skipUnless(os.environ.get('TCASFOLIO_SAMPLE_PDF'),
                         'set TCASFOLIO_SAMPLE_PDF to a real TCASFolio pdf (not committed: personal data)')
    def test_real_tcasfolio_sample_is_accepted(self):
        with open(os.environ['TCASFOLIO_SAMPLE_PDF'], 'rb') as f:
            content = f.read()

        self.assertEqual(verify.verify_with_profile(content, 'tcasfolio'), verify.OK)
        self.assertTrue(tcasfolio.validate(
            None, uploaded_file=SimpleUploadedFile('portfolio.pdf', content)).is_valid)


def load_import_project_uploaded_documents_script():
    scripts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    return importlib.import_module('import_project_uploaded_documents')


class ImportProjectUploadedDocumentsScriptTestCase(TestCase):

    HEADER = ['projects', 'rank', 'title', 'key', 'descriptions', 'specifications', 'notes',
              'extensions', 'prefix', 'size', 'type', 'required', 'detail', 'multiple',
              'majors', 'late', 'validator']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.script = load_import_project_uploaded_documents_script()

    def setUp(self):
        self.project = AdmissionProject.objects.create(title='Project A', short_title='A')
        self.other_project = AdmissionProject.objects.create(title='Project B', short_title='B')

    def row(self, key='portfolio', projects=None, required='1', majors=None, late=None,
            validator=None):
        items = [projects or str(self.project.id), '1', 'แฟ้มผลงาน', key, 'desc', 'PDF', '',
                 'PDF', '', '2000000', 'any', required, '0', '1']
        # old files have only the first 14 columns
        if majors is not None or late is not None or validator is not None:
            items += [majors or '', late or '', validator or '']
        return items

    def import_rows(self, *rows):
        return self.script.import_rows([self.HEADER] + list(rows))

    def test_new_columns_are_imported(self):
        self.import_rows(self.row(majors='1, 3', late='1', validator='tcasfolio'))

        doc = ProjectUploadedDocument.objects.get(document_key='portfolio')
        self.assertEqual(doc.major_numbers, '1,3')
        self.assertTrue(doc.is_late_upload_allowed)
        self.assertEqual(doc.validator, 'tcasfolio')
        self.assertTrue(doc.is_required)
        self.assertEqual(doc.document_type, ProjectUploadedDocument.DOCUMENT_TYPE_ANY)
        self.assertEqual(list(doc.admission_projects.all()), [self.project])

    def test_old_fourteen_column_rows_get_defaults(self):
        self.assertEqual(self.import_rows(self.row()), 1)

        doc = ProjectUploadedDocument.objects.get(document_key='portfolio')
        self.assertEqual(doc.major_numbers, '')
        self.assertFalse(doc.is_late_upload_allowed)
        self.assertEqual(doc.validator, '')

    def test_plain_requirement_key_is_an_or_group(self):
        self.import_rows(self.row(required='portfolio-or-clip'))

        doc = ProjectUploadedDocument.objects.get(document_key='portfolio')
        self.assertEqual(doc.requirement_key, 'portfolio-or-clip')
        self.assertFalse(doc.is_required)

    def test_rows_update_the_slot_with_the_same_document_key(self):
        self.import_rows(self.row(majors='1'))
        self.import_rows(self.row(majors='2'))

        self.assertEqual(ProjectUploadedDocument.objects.filter(document_key='portfolio').count(), 1)
        self.assertEqual(ProjectUploadedDocument.objects.get(document_key='portfolio').major_numbers, '2')

    def assert_rejected(self, bad_row, message):
        with self.assertRaisesRegex(self.script.RowError, message):
            self.import_rows(self.row(key='good'), bad_row)
        # the whole file is one transaction
        self.assertFalse(ProjectUploadedDocument.objects.exists())

    def test_conditional_if_key_is_rejected(self):
        self.assert_rejected(self.row(key='bad', required='if-%d-1' % self.project.id),
                             r'line 3: conditional requirement key')

    def test_major_numbers_with_several_projects_is_rejected(self):
        projects = '%d,%d' % (self.project.id, self.other_project.id)
        self.assert_rejected(self.row(key='bad', projects=projects, majors='1'),
                             'exactly one project')

    def test_invalid_major_numbers_is_rejected(self):
        self.assert_rejected(self.row(key='bad', majors='1-3'), 'invalid major_numbers')

    def test_unknown_validator_is_rejected(self):
        self.assert_rejected(self.row(key='bad', validator='tcasfolo'), 'unknown validator')

    def test_unknown_project_is_rejected(self):
        self.assert_rejected(self.row(key='bad', projects='999999'), 'unknown project id')


class MajorNoticesTestCase(TestCase):
    """Applicants see AdmissionCriteria.additional_notice for each selected
    major, read live from the criteria (no sync step). Multi-major projects
    show it in the major list; single-major projects in the details section."""

    def setUp(self):
        from appl.models import Campus, Faculty
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        self.faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test',
            is_additional_notice_allowed=True, max_num_selections=2)
        self.code_counter = 0
        self.major1, self.cm1 = self._major(1, 'วิศวกรรมคอมพิวเตอร์')
        self.major2, self.cm2 = self._major(2, 'วิศวกรรมไฟฟ้า')

    def _major(self, number, title):
        from appl.models import Major
        from criteria.models import CurriculumMajor, MajorCuptCode
        self.code_counter += 1
        program_code = '100201042123%03d' % self.code_counter
        cupt_code = MajorCuptCode.objects.create(
            program_code=program_code, program_type='ภาษาไทย ปกติ',
            program_type_code='1', faculty=self.faculty, title=title)
        major = Major.objects.create(
            number=number, title=title, faculty=self.faculty,
            admission_project=self.project, slots=10, detail_items_csv='',
            cupt_full_code=program_code)
        curriculum_major = CurriculumMajor.objects.create(
            admission_project=self.project, cupt_code=cupt_code, faculty=self.faculty)
        return major, curriculum_major

    def _criteria(self, curriculum_major, additional_notice, is_deleted=False):
        from criteria.models import AdmissionCriteria, CurriculumMajorAdmissionCriteria
        admission_criteria = AdmissionCriteria.objects.create(
            admission_project=self.project, faculty=self.faculty, version=1,
            additional_notice=additional_notice, is_deleted=is_deleted)
        CurriculumMajorAdmissionCriteria.objects.create(
            curriculum_major=curriculum_major,
            admission_criteria=admission_criteria, slots=1)
        return admission_criteria

    def _selection(self, *majors):
        selection = MajorSelection(admission_project=self.project)
        selection.majors = list(majors)
        return selection

    def _load(self, selection):
        from appl.views import load_major_notices
        load_major_notices(self.project, selection)

    def test_collects_non_blank_notices_from_live_criteria(self):
        self._criteria(self.cm1, '  ประกาศแรก\n')
        self._criteria(self.cm1, '   ')
        self._criteria(self.cm1, 'ประกาศที่สอง')
        self._criteria(self.cm1, 'เกณฑ์เก่า', is_deleted=True)
        selection = self._selection(self.major1, self.major2)

        self._load(selection)

        self.assertEqual(self.major1.notices, ['ประกาศแรก', 'ประกาศที่สอง'])
        self.assertEqual(self.major2.notices, [])

    def test_reflects_criteria_edits_without_sync(self):
        criteria = self._criteria(self.cm1, 'ก่อนแก้')
        criteria.additional_notice = 'หลังแก้'
        criteria.save()
        selection = self._selection(self.major1)

        self._load(selection)

        self.assertEqual(self.major1.notices, ['หลังแก้'])

    def test_major_without_cupt_code_has_no_notices(self):
        self.major1.cupt_full_code = ''
        self.major1.save()
        selection = self._selection(self.major1)

        self._load(selection)

        self.assertEqual(self.major1.notices, [])

    def test_not_loaded_when_project_flag_is_off(self):
        self.project.is_additional_notice_allowed = False
        self._criteria(self.cm1, 'ประกาศ')
        selection = self._selection(self.major1)

        self._load(selection)

        self.assertFalse(hasattr(self.major1, 'notices'))

    def _render(self, template, selection):
        from appl.models import ProjectApplication
        from appl.models import Major
        active_application = ProjectApplication(admission_project=self.project)
        # the major detail list needs a real detail_items_csv + project template,
        # which is unrelated to notices
        with mock.patch.object(Major, 'get_detail_items_as_list_display', return_value=''):
            return render_to_string(template,
                                    {'major_selection': selection,
                                     'active_application': active_application,
                                     'admission_round': AdmissionRound(id=1),
                                     'is_deadline_passed': True})

    def test_multi_major_list_shows_notice_next_to_each_major(self):
        self._criteria(self.cm1, 'บรรทัดแรก\nบรรทัดที่สอง')
        self._criteria(self.cm2, 'ประกาศสาขาสอง')
        selection = self._selection(self.major1, self.major2)
        self._load(selection)

        html = self._render('appl/include/major_selection_item.html', selection)

        self.assertIn('บรรทัดแรก<br>บรรทัดที่สอง', html)
        self.assertIn('ประกาศสาขาสอง', html)
        self.assertEqual(html.count('alert-info'), 2)

    def test_single_major_list_does_not_show_notice(self):
        self.project.max_num_selections = 1
        self._criteria(self.cm1, 'ประกาศ')
        selection = self._selection(self.major1)
        self._load(selection)

        html = self._render('appl/include/major_selection_item.html', selection)

        self.assertNotIn('ประกาศ</', html)
        self.assertNotIn('alert-info', html)

    def test_single_major_details_shows_notice(self):
        self.project.max_num_selections = 1
        self._criteria(self.cm1, 'ประกาศ')
        selection = self._selection(self.major1)
        self._load(selection)

        html = self._render('appl/include/selected_major_details.html', selection)

        self.assertIn('alert-info', html)
        self.assertIn('ประกาศ', html)


class ApplicationCompleteTestCase(TestCase):
    """The "ใบสมัครของคุณสมบูรณ์แล้ว" notice: shown when a major is selected,
    documents (incl. imported per-major questions) are complete and nothing is
    left to pay; hidden once results are shown. It lives in the status box that
    the upload JS refreshes through appl:check-project-documents."""

    NOTICE = 'ใบสมัครของคุณสมบูรณ์แล้ว'
    HIDDEN_NOTICE_DIV = 'id="application_complete_notice_div_id" style="display: none;"'

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
        from appl.models import Campus, Faculty, Major
        self.admission_round = AdmissionRound.objects.create(
            number=2, rank=1, is_available=True,
            acceptance_result_date=datetime.now().date())
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test', base_fee=400,
            max_num_selections=1)
        self.project_round = AdmissionProjectRound.objects.create(
            admission_project=self.project,
            admission_round=self.admission_round,
            is_started=True,
            applying_deadline=datetime.now() + timedelta(days=7),
            payment_deadline=(datetime.now() + timedelta(days=10)).date())
        campus = Campus.objects.create(title='Bang Khen', short_title='BK')
        faculty = Faculty.objects.create(title='Engineering', campus=campus)
        self.major = Major.objects.create(
            number=1, title='วิศวกรรมคอมพิวเตอร์', faculty=faculty,
            admission_project=self.project, slots=10, detail_items_csv='')

        self.applicant = Applicant.objects.create(
            national_id='1234567890121', prefix='นาย',
            first_name='ทดสอบ', last_name='มาก', email='test@test.com')
        self.application = self.applicant.apply_to_project(self.project,
                                                           self.admission_round)

        session = self.client.session
        session['applicant_id'] = self.applicant.id
        session.save()

    def select_major(self):
        MajorSelection.objects.create(
            applicant=self.applicant, project_application=self.application,
            admission_project=self.project, admission_round=self.admission_round,
            major_list=str(self.major.number), num_selected=1)

    def pay(self, amount=400):
        from appl.models import Payment
        Payment.objects.create(
            applicant=self.applicant, admission_round=self.admission_round,
            national_id=self.applicant.national_id, verification_number='x',
            amount=amount, paid_at=datetime.now())

    def make_required_document(self):
        doc = ProjectUploadedDocument.objects.create(
            rank=1, title='ใบรับรอง', descriptions='', specifications='PDF',
            allowed_extentions='PDF', document_type=FILE, is_required=True)
        doc.admission_projects.add(self.project)
        return doc

    def upload(self, doc):
        response = self.client.post(
            reverse('appl:upload', args=[doc.id]),
            {'uploaded_file': SimpleUploadedFile('a.pdf', b'%PDF-1.4 hello')})
        self.assertEqual(json.loads(response.content)['result'], 'OK')

    def add_question(self):
        from appl.models import MajorAdditionalAdmissionFormField
        self.project.is_additional_admission_form_allowed = True
        self.project.save()
        return MajorAdditionalAdmissionFormField.objects.create(
            major=self.major, admission_project=self.project,
            title='ทำไมถึงเลือกสาขานี้', size='short', rank=1)

    def status_html(self):
        response = self.client.get(reverse('appl:check-project-documents'))
        self.assertEqual(response.status_code, 200)
        return response.content.decode('utf-8')

    def assert_status_flag(self, flag):
        # the notice itself is outside the status box; the refresh JS shows or
        # hides it from this flag
        html = self.status_html()
        self.assertIn('data-application-complete="%s"' % flag, html)
        self.assertNotIn(self.NOTICE, html)

    def index_html(self):
        # index redirects to the profile forms without profiles, and the major
        # details need a real detail_items_csv; both are unrelated to the notice
        from appl.models import Major
        with mock.patch.object(Applicant, 'get_personal_profile', return_value=object()), \
             mock.patch.object(Applicant, 'get_educational_profile', return_value=object()), \
             mock.patch.object(Major, 'get_detail_items_as_list_display', return_value=''):
            response = self.client.get(reverse('appl:index'))
        self.assertEqual(response.status_code, 200)
        return response.content.decode('utf-8')

    # --- the rule ------------------------------------------------------------

    def test_is_application_complete(self):
        from appl.views import is_application_complete
        done = {'status': True, 'errors': []}
        missing = {'status': False, 'errors': ['x']}
        selection = object()

        self.assertTrue(is_application_complete(selection, done, 0))
        self.assertFalse(is_application_complete(None, done, 0))
        self.assertFalse(is_application_complete(selection, missing, 0))
        self.assertFalse(is_application_complete(selection, done, 100))

    # --- status box (AJAX refresh) -------------------------------------------

    def test_complete_application_shows_notice(self):
        self.select_major()
        self.pay()

        self.assert_status_flag('1')

    def test_free_project_needs_no_payment(self):
        self.project.base_fee = 0
        self.project.save()
        self.select_major()

        self.assert_status_flag('1')

    def test_no_notice_without_major(self):
        self.pay()

        self.assert_status_flag('0')

    def test_no_notice_when_fee_is_not_fully_paid(self):
        self.select_major()
        self.pay(amount=200)

        self.assert_status_flag('0')

    def test_last_upload_after_payment_completes_application(self):
        doc = self.make_required_document()
        self.select_major()
        self.pay()
        self.assert_status_flag('0')

        self.upload(doc)

        self.assert_status_flag('1')

    def test_unanswered_imported_question_keeps_application_incomplete(self):
        from appl.models import ApplicantAdditionalAdmissionFormValue
        field = self.add_question()
        self.select_major()
        self.pay()
        self.assert_status_flag('0')

        ApplicantAdditionalAdmissionFormValue.objects.create(
            applicant=self.applicant, major=self.major, field=field, value='ชอบ')

        self.assert_status_flag('1')

    def test_no_notice_once_results_are_shown(self):
        self.select_major()
        self.pay()

        for flag in ['accepted_for_interview_result_shown', 'accepted_result_shown']:
            with self.subTest(flag=flag):
                flags = {'accepted_for_interview_result_shown': False,
                         'accepted_result_shown': False}
                flags[flag] = True
                AdmissionProjectRound.objects.filter(pk=self.project_round.pk).update(**flags)

                self.assert_status_flag('0')

    def test_status_refresh_hides_payment_buttons_after_payment_deadline(self):
        self.select_major()
        AdmissionProjectRound.objects.filter(pk=self.project_round.pk).update(
            payment_deadline=(datetime.now() - timedelta(days=3)).date())

        html = self.status_html()

        self.assertIn('หมดเขตชำระค่าสมัครแล้ว', html)
        self.assertNotIn(reverse('appl:payment-qr', args=[self.application.id]), html)

    # --- main page -----------------------------------------------------------

    def test_index_shows_notice_when_complete(self):
        self.select_major()
        html = self.index_html()
        # rendered hidden so the refresh JS can slide it down later
        self.assertIn(self.NOTICE, html)
        self.assertIn(self.HIDDEN_NOTICE_DIV, html)

        self.pay()

        html = self.index_html()
        self.assertIn(self.NOTICE, html)
        self.assertIn('id="application_complete_notice_div_id"', html)
        self.assertNotIn(self.HIDDEN_NOTICE_DIV, html)

    def test_index_shows_notice_above_the_status_box(self):
        self.select_major()
        self.pay()

        html = self.index_html()

        self.assertLess(html.index('id="application_complete_notice_div_id"'),
                        html.index('id="project_status_div_id"'))
