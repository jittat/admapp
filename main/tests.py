import os

from django.conf import settings
from django.test import SimpleTestCase
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

    def test_switcher_keeps_query_string(self):
        response = self.client.get('/en/?error=invalid')
        self.assertContains(response, 'href="/?error=invalid"')
