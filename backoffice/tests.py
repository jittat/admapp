# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase


class BackofficeLogoutTestCase(TestCase):
    """Logout for backoffice staff users.

    Django's LogoutView is POST-only since Django 5.0 (GET was deprecated in
    4.1), so the navbar link must submit a form, not be a plain anchor.
    """

    TEST_USERNAME = 'staff1'
    TEST_PASSWORD = 'testpass1234'

    def setUp(self):
        User.objects.create_user(username=self.TEST_USERNAME,
                                 password=self.TEST_PASSWORD)
        self.client.login(username=self.TEST_USERNAME,
                          password=self.TEST_PASSWORD)

    def test_logout_with_post(self):
        response = self.client.post('/accounts/logout/')

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_with_get_is_not_allowed(self):
        response = self.client.get('/accounts/logout/')

        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_backoffice_page_has_logout_form(self):
        response = self.client.get('/backoffice/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<form class="nav-item form-inline" action="/accounts/logout/" method="post">')
        self.assertNotContains(response, 'href="/accounts/logout/"')


class ApplicantUploadedDocMenuTestCase(SimpleTestCase):
    """The document menu on the staff applicant page
    (projects/include/applicant_uploaded_doc_menu.html), rendered directly
    with unsaved slots/uploads."""

    TEMPLATE = 'backoffice/projects/include/applicant_uploaded_doc_menu.html'

    def render_menu(self, *docs):
        from types import SimpleNamespace
        from django.template.loader import render_to_string
        return render_to_string(self.TEMPLATE, {
            'uploaded_documents': list(docs),
            'project': SimpleNamespace(id=1),
            'admission_round': SimpleNamespace(id=2),
            'major': SimpleNamespace(number=3),
            'applicant': SimpleNamespace(national_id='1234567890123'),
        })

    def make_slot(self, pk, title, uploads, multiple=True):
        from appl.models import ProjectUploadedDocument
        slot = ProjectUploadedDocument(id=pk, title=title,
                                       document_type='any',
                                       can_have_multiple_files=multiple)
        slot.applicant_uploaded_documents = uploads
        return slot

    def make_file(self, pk, name='doc.pdf', detail=''):
        from appl.models import UploadedDocument
        return UploadedDocument(id=pk, uploaded_file=name, detail=detail)

    def make_link(self, pk, url, local_url='', detail=''):
        from appl.models import UploadedDocument
        return UploadedDocument(id=pk, document_url=url,
                                local_document_url=local_url, detail=detail)

    def test_empty_slot_is_listed_as_missing(self):
        html = self.render_menu(self.make_slot(10, 'Transcript', []))
        self.assertIn('Transcript (ไม่มีเอกสาร)', html)

    def test_mixed_slot_labels_files_and_links(self):
        html = self.render_menu(self.make_slot(10, 'Portfolio', [
            self.make_file(20, detail='scan'),
            self.make_link(21, 'https://folio.mytcas.com/view-folio/abc'),
        ]))
        self.assertIn('/doc/1234567890123/10/20/', html)
        self.assertIn('>ไฟล์</span>', html)
        self.assertIn('>ลิงก์</span>', html)
        self.assertIn('title="https://folio.mytcas.com/view-folio/abc"', html)
        self.assertNotIn('ไม่มีเอกสาร', html)

    def test_multiple_links_prefer_local_url(self):
        html = self.render_menu(self.make_slot(10, 'Portfolio', [
            self.make_link(21, 'https://example.com/a', local_url='https://local.example/a'),
            self.make_link(22, 'https://example.com/b'),
        ]))
        self.assertIn('href="https://local.example/a"', html)
        self.assertIn('title="https://example.com/a"', html)
        self.assertIn('href="https://example.com/b"', html)

    def test_single_link_has_count_badge(self):
        html = self.render_menu(self.make_slot(
            10, 'Folio', [self.make_link(21, 'https://example.com/a')], multiple=False))
        self.assertIn('<span class="badge badge-secondary">1</span>', html)
        self.assertIn('>ลิงก์</span>', html)
