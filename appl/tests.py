import json
import shutil
import tempfile
from datetime import datetime, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from appl.models import (AdmissionProject, AdmissionProjectRound, AdmissionRound,
                         ProjectUploadedDocument, UploadedDocument)
from appl.views.upload import get_upload_kind
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
                      is_detail_required=False):
        doc = ProjectUploadedDocument.objects.create(
            rank=1, title='เอกสาร', descriptions='', specifications='PDF',
            allowed_extentions='PDF', document_type=document_type,
            can_have_multiple_files=can_have_multiple_files,
            is_detail_required=is_detail_required)
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
