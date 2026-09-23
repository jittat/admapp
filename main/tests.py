import os
import re

from django.conf import settings
from django.template.loader import render_to_string
from django.test import RequestFactory, SimpleTestCase
from django.urls import set_script_prefix
from django.utils import translation


class MainTestCase(SimpleTestCase):

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class TranslationTestCase(SimpleTestCase):

    def test_locale_paths_are_absolute(self):
        # relative paths resolve against the process cwd, which breaks
        # translations when the app server runs from another directory
        for path in settings.LOCALE_PATHS:
            self.assertTrue(os.path.isabs(path), path)

    def test_english_catalog_is_loaded(self):
        # fails if locale/en/LC_MESSAGES/django.mo is missing or stale
        with translation.override('en'):
            self.assertEqual(translation.gettext('วิทยาเขตบางเขน'),
                             'Bangkhen Campus')
            self.assertEqual(
                translation.gettext('คุณผ่านการคัดเลือกมีสิทธิ์เข้าสอบสัมภาษณ์ ในสาขาต่อไปนี้'),
                'You have been accepted for an interview for the following major(s)')

    def test_html_lang_follows_active_language(self):
        self.assertContains(self.client.get('/'), '<html lang="th">')
        self.assertContains(self.client.get('/en/'), '<html lang="en">')


class LanguageSwitcherTestCase(SimpleTestCase):

    def test_switcher_links_to_same_page_in_other_language(self):
        self.assertContains(self.client.get('/'), 'href="/en/"')
        self.assertContains(self.client.get('/en/'), 'href="/"')
        self.assertContains(self.client.get('/regis/register/'),
                            'href="/en/regis/register/"')
        self.assertContains(self.client.get('/en/regis/register/'),
                            'href="/regis/register/"')

    def test_switcher_works_under_script_prefix(self):
        # production is deployed under /kuadm/; the test client
        # doesn't set the script prefix like the WSGI handler does
        set_script_prefix('/kuadm/')
        try:
            response = self.client.get('/regis/register/', SCRIPT_NAME='/kuadm')
            self.assertContains(response, 'href="/kuadm/en/regis/register/"')
            response = self.client.get('/en/regis/register/', SCRIPT_NAME='/kuadm')
            self.assertContains(response, 'href="/kuadm/regis/register/"')
        finally:
            set_script_prefix('/')

    def test_switcher_keeps_query_string(self):
        response = self.client.get('/en/?error=invalid')
        self.assertContains(response, 'href="/?error=invalid"')


class EnglishPagesTestCase(SimpleTestCase):
    """Applicant pages under /en/ should show no Thai text."""

    # Thai text that is meant to stay on English pages
    ALLOWED_THAI = [
        'ใช้ระบบรับสมัครเป็นภาษาไทย',   # link to the Thai version
    ]

    def assertNoThaiText(self, html):
        body = html.split('<body>', 1)[-1]
        text = re.sub(r'<[^>]*>', ' ', body)   # ignore tags and attribute values
        for allowed in self.ALLOWED_THAI:
            text = text.replace(allowed, '')
        self.assertEqual(re.findall(r'[฀-๿][^<>\n]*', text), [])

    def render_en(self, template_name, context):
        request = RequestFactory().get('/en/')
        with translation.override('en'):
            return render_to_string(template_name, context, request=request)

    def test_pages(self):
        for url in ['/en/', '/en/regis/register/', '/en/regis/forget/']:
            with self.subTest(url=url):
                self.assertNoThaiText(self.client.get(url).content.decode())

    def test_regis_result_pages(self):
        pages = [
            ('regis/regis_result.html', {'email': 'a@example.com'}),
            ('regis/registration_error.html',
             {'national_id': '1234567890123', 'first_name': 'A'}),
            ('regis/registration_error.html',
             {'national_id': '', 'passport_number': 'X1', 'first_name': 'A'}),
            ('regis/forget.html',
             {'update_success': True, 'email': 'a@example.com'}),
            ('regis/forget.html', {'error_message': 'x'}),
        ]
        for template_name, context in pages:
            with self.subTest(template=template_name, context=context):
                self.assertNoThaiText(self.render_en(template_name, context))
