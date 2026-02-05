from django.test import TestCase, override_settings

from regis.models import Applicant, LogItem


class RegistrationTestCase(TestCase):

    TEST_NATID = '1234567890121'
    TEST_PASSPORT_NUMBER = 'F102030'
    TEST_APP_PASSWORD = 'testpass1234'
    
    REGIS_FULL_DATA_NATID = {
        'has_national_id': '1',
        'national_id': TEST_NATID,
        'national_id_confirm': TEST_NATID,
        'passport_number': '',
        'passport_number_confirm': '',
        'email': 'test@test.com',
        'email_confirm': 'test@test.com',
        'prefix': 'นาย',
        'first_name': 'ทดสอบ',
        'last_name': 'มาก',
        'password': TEST_APP_PASSWORD,
        'password_confirm': TEST_APP_PASSWORD,
    }

    
    def setUp(self):
        self.regis_full_data_natid = self.REGIS_FULL_DATA_NATID.copy()
        

    def test_register_index(self):
        response = self.client.get('/regis/register/')
        self.assertEqual(response.status_code, 200)


    def test_register_with_nat_id(self):
        response = self.register_test_applicant(self.client)
        self.assertTemplateUsed(response, 'regis/regis_result.html')

        a = Applicant.objects.get(national_id=self.TEST_NATID)
        self.assertIsNotNone(a)

        
    def test_register_with_bad_confirm_nat_id(self):
        data = self.regis_full_data_natid.copy()
        data['national_id_confirm'] = '1234567890139'
        response = self.client.post('/regis/register/',
                                    data)
        self.assertFormError(response,'form','national_id_confirm','รหัสประจำตัวประชาชนที่ยืนยันไม่ตรงกัน')

    @override_settings(FAKE_LOGIN=False)
    def test_login_with_nat_id(self):
        self.register_test_applicant(self.client)

        response = self.client.post('/regis/login/',
                                    { 'national_id': self.TEST_NATID,
                                      'password': self.TEST_APP_PASSWORD })
        self.assertRedirects(response, 
                             '/appl/',
                             fetch_redirect_response=False)
        
    @override_settings(FAKE_LOGIN=False)
    def test_login_failed_with_nat_id(self):
        self.register_test_applicant(self.client)
        response = self.client.post('/regis/login/',
                                    { 'national_id': self.TEST_NATID,
                                      'password': self.TEST_APP_PASSWORD + 'xx' })
        self.assertRedirects(response, '/?error=wrong-password')
        
        
    @override_settings(FAKE_LOGIN=False)
    def test_login_with_passport_number(self):
        self.register_test_applicant_with_passport_number(self.client)

        response = self.client.post('/regis/login/',
                                    { 'national_id': self.TEST_PASSPORT_NUMBER,
                                      'password': self.TEST_APP_PASSWORD })
        self.assertRedirects(response, 
                             '/appl/', 
                             fetch_redirect_response=False)

    @override_settings(FAKE_LOGIN=False)
    def test_login_with_passport_number(self):
        self.register_test_applicant_with_passport_number(self.client)

        response = self.client.post('/regis/login/',
                                    { 'national_id': self.TEST_PASSPORT_NUMBER,
                                      'password': self.TEST_APP_PASSWORD+'xx' })
        self.assertRedirects(response, '/?error=wrong-password')
        
        
    def test_logout(self):
        self.register_test_applicant(self.client)
        self.login_test_applicant(self.client)

        response = self.client.get('/regis/logout/')

        response = self.client.get('/appl/')
        self.assertRedirects(response, '/?error=no-login')

    def test_register_with_no_has_national_id(self):
        from regis.views import RuntimeErrorNoLogging
        from regis.views import register

        register.sending_mail_prob = 0

        data = self.regis_full_data_natid.copy()
        del data['has_national_id']
        try:
            response = self.client.post('/regis/register/',
                                        data)
        except RuntimeErrorNoLogging:
            pass
        except:
            self.fail('Expected RuntimeErrorNoLogging exception')
        self.assertEqual(LogItem.objects.filter(message__contains='error').count(), 1)

    def test_register_with_empty_has_national_id(self):
        from regis.views import RuntimeErrorNoLogging
        from regis.views import register

        register.sending_mail_prob = 0

        data = self.regis_full_data_natid.copy()
        data['has_national_id'] = ''
        try:
            response = self.client.post('/regis/register/',
                                        data)
        except RuntimeErrorNoLogging:
            pass
        except:
            self.fail('Expected RuntimeErrorNoLogging exception')
        self.assertEqual(LogItem.objects.filter(message__contains='error').count(), 1)

    @staticmethod
    def register_test_applicant(client):
        response = client.post('/regis/register/',
                               RegistrationTestCase.REGIS_FULL_DATA_NATID)
        return response

    @staticmethod
    def login_test_applicant(client):
        response = client.post('/regis/login/',
                               { 'national_id': RegistrationTestCase.TEST_NATID,
                                 'password': RegistrationTestCase.TEST_APP_PASSWORD })
        return response

        
    @staticmethod
    def register_test_applicant_with_passport_number(client):
        RegistrationTestCase.register_test_applicant(client)
        a = Applicant.objects.get(national_id=RegistrationTestCase.TEST_NATID)
        a.passport_number = RegistrationTestCase.TEST_PASSPORT_NUMBER;
        a.save()
