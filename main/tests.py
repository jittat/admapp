import os
import re
from django.conf import settings
from django.template.loader import render_to_string
from datetime import date, datetime, timedelta

from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
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
            self.assertEqual(translation.gettext('รอบที่ %(number)s'),
                             'Round %(number)s')
            self.assertEqual(
                translation.gettext('คุณมีสิทธิ์เข้าสอบสัมภาษณ์ ในสาขาต่อไปนี้'),
                'You are eligible for an interview for the following major(s)')

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


class ApplicantFixturesMixin:
    """A logged-in applicant with profiles, and an open project in an
    available round. DB titles are Thai with English title_en set."""

    def setUp(self):
        from appl.models import (AdmissionProject, AdmissionProjectRound,
                                 AdmissionRound, EducationalProfile,
                                 PersonalProfile, Province)
        from regis.models import Applicant

        self.admission_round = AdmissionRound.objects.create(
            number=2, rank=1, is_available=True,
            acceptance_result_date=date.today())
        self.project = AdmissionProject.objects.create(
            title='โครงการทดสอบ', title_en='Test Project', short_title='Test',
            is_available=True)
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

    def apply_with_majors(self, max_num_selections):
        from appl.models import Campus, Faculty, Major
        self.project.max_num_selections = max_num_selections
        self.project.column_descriptions = '* Details'
        self.project.save()
        campus = Campus.objects.create(title='วิทยาเขตบางเขน', short_title='บางเขน',
                                       title_en='Bangkhen Campus')
        faculty = Faculty.objects.create(title='คณะวิศวกรรมศาสตร์', campus=campus,
                                         title_en='Faculty of Engineering')
        majors = [Major.objects.create(number=i, title='สาขา %d' % i, title_en='Major %d' % i,
                                       faculty=faculty,
                                       admission_project=self.project, slots=10,
                                       detail_items_csv='Major details')
                  for i in (1, 2)]
        application = self.applicant.apply_to_project(self.project,
                                                      self.admission_round)
        return application, majors


class EnglishApplPagesTestCase(ApplicantFixturesMixin, NoThaiTextMixin, TestCase):
    """appl pages under /en/ for a logged-in applicant."""

    def test_pages(self):
        for url in ['/en/appl/', '/en/appl/personal/', '/en/appl/education/']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNoThaiText(response.content.decode())

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

    def assert_major_selection_page(self, max_num_selections):
        self.apply_with_majors(max_num_selections)
        response = self.client.get('/en/appl/select/%d/' % self.admission_round.id)
        self.assertEqual(response.status_code, 200)
        self.assertNoThaiText(response.content.decode())

    def test_major_selection_page(self):
        self.assert_major_selection_page(1)

    def test_major_multiple_selection_page(self):
        self.assert_major_selection_page(2)

    def test_major_selection_errors(self):
        from appl.views.major_selection import process_selection_form
        application, majors = self.apply_with_majors(2)
        request = RequestFactory().post('/', {'major': ['99']})
        with translation.override('en'):
            error, message = process_selection_form(request, self.applicant,
                                                    application, None)
        self.assertEqual((error, message), (True, 'Invalid major choice'))

    def test_major_includes(self):
        from appl.models import MajorAdditionalAdmissionFormField, MajorSelection
        application, majors = self.apply_with_majors(2)
        major_selection = MajorSelection.objects.create(
            applicant=self.applicant, project_application=application,
            admission_project=self.project, admission_round=self.admission_round,
            major_list='1,2', num_selected=2)
        major = majors[0]
        major.form_fields = [
            MajorAdditionalAdmissionFormField.objects.create(
                major=major, admission_project=self.project,
                title='Why this major?', size=size, rank=rank)
            for rank, size in ((1, 'short'), (2, 'paragraph'))]
        for f in major.form_fields:
            f.value = None
        for m in majors:
            m.is_accepted_for_interview = (m == major)
        pages = [
            ('appl/include/major_selection_item.html',
             {'active_application': application, 'admission_round': self.admission_round,
              'major_selection': major_selection}),
            ('appl/include/major_selection_item.html',
             {'active_application': application, 'admission_round': self.admission_round,
              'major_selection': major_selection, 'is_deadline_passed': True,
              'accepted_for_interview_result_shown': True}),
            ('appl/include/major_selection_item.html',
             {'active_application': application, 'admission_round': self.admission_round,
              'major_selection': None}),
            ('appl/include/major_additional_form.html', {'major': major}),
        ]
        for template_name, context in pages:
            with self.subTest(template=template_name):
                self.assertNoThaiText(self.render_en(template_name, context))

    def test_major_hidden_info_link(self):
        from appl.models import Major
        major = Major(number=1)
        with translation.override('en'):
            html = major.process_hidden_info('a\n--info-start--\nb\n--info-end--')
        self.assertIn('>Show details</a>', html)

    def test_upload_and_status_includes(self):
        from appl.models import AdmissionProject, ProjectUploadedDocument, UploadedDocument
        from appl.views.upload import prepare_deadline_flags
        self.project.base_fee = 400
        application, majors = self.apply_with_majors(1)
        tomorrow = date.today() + timedelta(days=1)

        def upload_slot(document_type, uploaded, **kwargs):
            doc = ProjectUploadedDocument(
                id=7, rank=1, title='Portfolio', descriptions='', specifications='PDF',
                allowed_extentions='PDF', document_type=document_type, **kwargs)
            doc.applicant_uploaded_documents = uploaded
            prepare_deadline_flags(doc, AdmissionProject(late_upload_date=tomorrow))
            return doc

        uploaded = [UploadedDocument(id=1, detail='a.pdf',
                                     uploaded_file='documents/applicant_3/doc_7/a.pdf'),
                    UploadedDocument(id=2, detail='link',
                                     document_url='http://example.com/portfolio')]
        status = {'active_application': application,
                  'payment_deadline': tomorrow, 'paid_amount': 0,
                  'additional_payment': application.admission_fee()}
        pages = [
            ('appl/include/document_upload_js.html', {}),
            ('appl/include/document_upload_form.html',
             {'project_uploaded_document': upload_slot(
                 ProjectUploadedDocument.DOCUMENT_TYPE_ANY, uploaded[:1]),
              'applicant': self.applicant, 'toggle': 'show'}),
            ('appl/include/document_upload_form.html',
             {'project_uploaded_document': upload_slot(
                 ProjectUploadedDocument.DOCUMENT_TYPE_ANY, uploaded,
                 can_have_multiple_files=True, is_detail_required=True),
              'applicant': self.applicant, 'toggle': 'show'}),
            ('appl/include/document_upload_form.html',
             {'project_uploaded_document': upload_slot(
                 ProjectUploadedDocument.DOCUMENT_TYPE_URL, [], is_late_upload_allowed=True),
              'applicant': self.applicant, 'toggle': 'show', 'is_deadline_passed': True}),
            ('appl/include/old_document_upload_list.html', {}),
            ('appl/include/application_complete_notice.html', {}),
            ('appl/include/application_document_status.html',
             dict(status, documents_complete_status={'status': False, 'errors': ['x']},
                  paid_amount=100)),
            ('appl/include/application_document_status.html',
             dict(status, documents_complete_status={'status': True}, major_selection=None)),
            ('appl/include/application_document_status.html',
             dict(status, documents_complete_status={'status': True}, major_selection=True)),
            ('appl/include/application_document_status.html',
             dict(status, documents_complete_status={'status': True}, major_selection=True,
                  payment_deadline_passed=True)),
        ]
        for template_name, context in pages:
            with self.subTest(template=template_name, context=context):
                self.assertNoThaiText(self.render_en(template_name, context))
        # the payment options are rendered, not skipped
        self.assertIn('Pay by QR code', self.render_en(*pages[-2]))
        self.assertIn('payment deadline has passed', self.render_en(*pages[-1]))

    def test_document_validation_messages(self):
        from appl.document_validators import ValidationResult
        from appl.models import ProjectUploadedDocument
        from appl.views.upload import render_validation_message
        codes = ['not_pdf', 'not_signed', 'modified_after_signing', 'untrusted_signer',
                 'invalid_url', 'no_document', 'misconfigured', 'bad_file']
        for validator in ('tcasfolio', 'default'):
            for code in codes:
                with self.subTest(validator=validator, code=code), translation.override('en'):
                    html = render_validation_message(
                        ProjectUploadedDocument(validator=validator),
                        ValidationResult.reject(code), None)
                    self.assertNoThaiText(html)


# Seasonal hook templates stay Thai for now (see docs/i18n-status.md), so
# the result-page tests render them empty.
HOOK_TEMPLATES = [
    'appl/include/interview_application_print_hook.html',
    'appl/include/paper_application_print_hook.html',
    'appl/include/project_accepted_for_interview_result_info_hooks.html',
    'appl/include/project_accepted_result_acceptance_prehook.html',
    'appl/include/project_accepted_result_acceptance_posthook.html',
    'appl/include/special_cancel_hook.html',
]
WITHOUT_HOOKS = override_settings(TEMPLATES=[{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'OPTIONS': {
        'context_processors': settings.TEMPLATES[0]['OPTIONS']['context_processors'],
        'loaders': [
            ('django.template.loaders.locmem.Loader',
             {name: '' for name in HOOK_TEMPLATES}),
            'django.template.loaders.app_directories.Loader',
        ],
    },
}])


@WITHOUT_HOOKS
class EnglishResultPagesTestCase(ApplicantFixturesMixin, NoThaiTextMixin, TestCase):
    """The dashboard after applying, including interview and admission
    results."""

    def setUp(self):
        super().setUp()
        from appl.models import MajorSelection
        self.application, majors = self.apply_with_majors(1)
        self.major = majors[0]
        MajorSelection.objects.create(
            applicant=self.applicant, project_application=self.application,
            admission_project=self.project, admission_round=self.admission_round,
            major_list='1', num_selected=1)
        self.project_round = self.project.get_project_round_for(self.admission_round)

    def show_results(self, is_accepted_for_interview, is_accepted=None):
        from appl.models import AdmissionResult
        self.project_round.accepted_for_interview_result_shown = True
        self.project_round.accepted_result_shown = is_accepted is not None
        self.project_round.save()
        AdmissionResult.objects.create(
            applicant=self.applicant, application=self.application,
            admission_project=self.project, admission_round=self.admission_round,
            major=self.major, is_accepted_for_interview=is_accepted_for_interview,
            is_accepted=is_accepted, interview_rank=3)

    def add_interview_description(self, interview_options):
        from appl.models import MajorInterviewDescriptionCache
        from backoffice.models import InterviewDescription
        description = InterviewDescription.objects.create(
            admission_round=self.admission_round, admission_project=self.project,
            major=self.major, faculty=self.major.faculty,
            interview_options=interview_options,
            video_conference_platform='zoom',
            interview_date=datetime(2026, 2, 25, 9, 0),
            additional_documents_option=InterviewDescription.OPTION_DOC_UPLOAD_ON_ADMAPP,
            contacts=[{'name': 'Staff', 'tel': '021234567', 'email': 'a@example.com'}])
        MajorInterviewDescriptionCache.objects.create(
            major=self.major, interview_description=description)

    def assert_index_has_no_thai(self):
        response = self.client.get('/en/appl/')
        self.assertEqual(response.status_code, 200)
        self.assertNoThaiText(response.content.decode())
        return response

    def test_active_application(self):
        self.assert_index_has_no_thai()

    def test_accepted_for_interview(self):
        from backoffice.models import InterviewDescription
        self.show_results(True)
        self.add_interview_description(InterviewDescription.OPTION_ONLINE_INTERVIEW)
        response = self.assert_index_has_no_thai()
        self.assertContains(response, 'Interview information')
        self.assertContains(response, '25 February 2026')

    def test_not_accepted_for_interview(self):
        self.show_results(False)
        self.assert_index_has_no_thai()

    def test_accepted(self):
        self.show_results(True, is_accepted=True)
        response = self.assert_index_has_no_thai()
        self.assertContains(response, 'are admitted to')

    def test_not_accepted(self):
        self.show_results(True, is_accepted=False)
        self.assert_index_has_no_thai()

    def test_next_round_announcement(self):
        html = self.render_en('appl/include/next_round_announcement.html',
                              {'active_application': self.application})
        self.assertNoThaiText(html)
        self.assertIn('Round 2', html)

    def test_cupt_confirmation_includes(self):
        for name in ['cupt_confirmation_not_free', 'cupt_confirmation_not_registered',
                     'cupt_confirmation_wait']:
            with self.subTest(template=name):
                self.assertNoThaiText(self.render_en('appl/include/%s.html' % name, {}))


class TitleTransTestCase(SimpleTestCase):

    def test_title_trans_uses_title_en_on_english_pages(self):
        from appl.models import AdmissionProject, Campus, Faculty, Major
        for model in (AdmissionProject, Campus, Faculty, Major):
            with self.subTest(model=model.__name__):
                obj = model(title='ไทย', title_en='English')
                with translation.override('th'):
                    self.assertEqual(obj.title_trans(), 'ไทย')
                with translation.override('en'):
                    self.assertEqual(obj.title_trans(), 'English')
                obj.title_en = ''
                with translation.override('en'):
                    self.assertEqual(obj.title_trans(), 'ไทย')

    def test_campus_short_title(self):
        from appl.models import Campus
        campus = Campus(title='วิทยาเขตบางเขน', short_title='บางเขน',
                        title_en='Bangkhen Campus')
        with translation.override('th'):
            self.assertEqual(campus.short_title_trans(), 'บางเขน')
        with translation.override('en'):
            self.assertEqual(campus.short_title_trans(), 'Bangkhen Campus')

    def test_round_title(self):
        from appl.models import AdmissionRound
        with translation.override('th'):
            self.assertEqual(AdmissionRound(number=2, subround_number=0).title_trans(),
                             'รอบที่ 2')
            self.assertEqual(AdmissionRound(number=1, subround_number=2).title_trans(),
                             'รอบที่ 1.2')
        with translation.override('en'):
            self.assertEqual(AdmissionRound(number=1, subround_number=2).title_trans(),
                             'Round 1.2')


class ThaiDateFilterTestCase(SimpleTestCase):

    def test_thaidate_follows_language(self):
        from appl.templatetags.appl_tags import thaidate
        d = date(2026, 9, 24)
        with translation.override('th'):
            self.assertEqual(thaidate(d), '24 กันยายน 2569')
        with translation.override('en'):
            self.assertEqual(thaidate(d), '24 September 2026')
