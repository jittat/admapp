import os
import re
from django.conf import settings
from django.template.loader import render_to_string
from datetime import date, datetime, timedelta

from django.test import RequestFactory, SimpleTestCase, TestCase
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


class NoThaiTextMixin:
    # Thai text that is meant to stay on English pages
    ALLOWED_THAI = [
        'ใช้ระบบรับสมัครเป็นภาษาไทย',   # link to the Thai version
        "[{title: 'กรุงเทพ'}]",         # placeholder data in education.html JS
    ]

    def assertNoThaiText(self, html, ignore_scripts=False):
        body = html.split('<body>', 1)[-1]
        if ignore_scripts:
            body = re.sub(r'<script>.*?</script>', ' ', body, flags=re.DOTALL)
        text = re.sub(r'<[^>]*>', ' ', body)   # ignore tags and attribute values
        for allowed in self.ALLOWED_THAI:
            text = text.replace(allowed, '')
        self.assertEqual(re.findall(r'[฀-๿][^<>\n]*', text), [])

    def render_en(self, template_name, context):
        request = RequestFactory().get('/en/')
        with translation.override('en'):
            return render_to_string(template_name, context, request=request)


class EnglishPagesTestCase(NoThaiTextMixin, SimpleTestCase):
    """Applicant pages under /en/ should show no Thai text."""

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


class EnglishApplPagesTestCase(NoThaiTextMixin, TestCase):
    """appl pages under /en/ for a logged-in applicant.

    DB titles (project, round) are in English here; translating them is
    phase 2e. The page after applying is checked once its includes are
    translated (phase 2d)."""

    def setUp(self):
        from appl.models import (AdmissionProject, AdmissionProjectRound,
                                 AdmissionRound, EducationalProfile,
                                 PersonalProfile, Province)
        from regis.models import Applicant

        self.admission_round = AdmissionRound.objects.create(
            number=2, rank=1, is_available=True,
            acceptance_result_date=date.today())
        self.project = AdmissionProject.objects.create(
            title='Test Project', short_title='Test', is_available=True)
        AdmissionProjectRound.objects.create(
            admission_project=self.project,
            admission_round=self.admission_round,
            is_started=True,
            applying_deadline=datetime.now() + timedelta(days=7),
            payment_deadline=date.today() + timedelta(days=10))
        self.applicant = Applicant.objects.create(
            national_id='1234567890121', prefix='Mr.',
            first_name='Test', last_name='Applicant', email='test@test.com')
        province = Province.objects.create(title='Bangkok')
        PersonalProfile.objects.create(
            applicant=self.applicant, first_name_english='Test',
            last_name_english='Applicant', birthday=date(2008, 1, 2),
            father_prefix='Mr.', father_first_name='F', father_last_name='A',
            mother_prefix='Mrs.', mother_first_name='M', mother_last_name='A',
            house_number='1', sub_district='S', district='D',
            province='Bangkok', postal_code='10900', contact_phone='021234567')
        EducationalProfile.objects.create(
            applicant=self.applicant, education_level=1, education_plan=1,
            gpa=3.5, province=province, school_title='Test School')

        session = self.client.session
        session['applicant_id'] = self.applicant.id
        session.save()

    def test_pages(self):
        for url in ['/en/appl/', '/en/appl/personal/', '/en/appl/education/']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                # TODO(2c): the index includes document_upload_js.html
                self.assertNoThaiText(response.content.decode(),
                                      ignore_scripts=(url == '/en/appl/'))

    def test_project_list_uses_ce_admission_year(self):
        response = self.client.get('/en/appl/')
        self.assertContains(response,
                            'the %d academic year' % (settings.ADMISSION_YEAR - 543))
        response = self.client.get('/appl/')
        self.assertContains(response, 'ปีการศึกษา %d' % settings.ADMISSION_YEAR)

    def test_birthday_years_follow_language(self):
        self.assertContains(self.client.get('/en/appl/personal/'),
                            '<option value="2008" selected>2008</option>')
        self.assertContains(self.client.get('/appl/personal/'),
                            '<option value="2008" selected>2551</option>')

    def test_saved_notice(self):
        from appl.models import PersonalProfile
        data = {f.name: getattr(self.applicant.personalprofile, f.name)
                for f in PersonalProfile._meta.fields
                if f.name not in ('id', 'applicant', 'birthday')}
        data.update(birthday_day=2, birthday_month=1, birthday_year=2008)
        response = self.client.post('/en/appl/personal/', data, follow=True)
        self.assertContains(response, 'Personal information saved.')

    def test_includes(self):
        from appl.models import AdmissionProjectRound, AdmissionRound
        other_round = AdmissionRound.objects.create(
            number=3, rank=2, acceptance_result_date=date.today())
        AdmissionProjectRound.objects.create(
            admission_project=self.project, admission_round=other_round,
            applying_deadline=datetime.now() + timedelta(days=7),
            payment_deadline=date.today() + timedelta(days=10))
        application = self.applicant.apply_to_project(self.project, other_round)

        class Major:
            notices = ['Notice text']

        pages = [
            ('appl/include/form_instruction.html', {'instruction_step': 2}),
            ('appl/include/form_instruction.html', {'instruction_step': 3}),
            ('appl/include/other_application_rounds.html',
             {'admission_round': self.admission_round,
              'other_application_rounds': [(other_round, application)]}),
            ('appl/include/project_deadline_announcement.html', {}),
            ('appl/include/major_notices.html', {'major': Major()}),
            ('appl/include/project_supplement_link.html',
             {'active_application': application,
              'supplement_configs': [{'title': 'Form'}]}),
        ]
        for template_name, context in pages:
            with self.subTest(template=template_name, context=context):
                self.assertNoThaiText(self.render_en(template_name, context))

    def test_document_status_errors(self):
        from appl.views import check_project_documents

        class Config:
            is_required = True
            supplement_instance = None
            title = 'Form'

        with translation.override('en'):
            status = check_project_documents(self.applicant, self.project,
                                             [Config()], [], None)
        self.assertEqual(status['errors'], ['Not filled in yet: Form'])


class ThaiDateFilterTestCase(SimpleTestCase):

    def test_thaidate_follows_language(self):
        from appl.templatetags.appl_tags import thaidate
        d = date(2026, 9, 24)
        with translation.override('th'):
            self.assertEqual(thaidate(d), '24 กันยายน 2569')
        with translation.override('en'):
            self.assertEqual(thaidate(d), '24 September 2026')
