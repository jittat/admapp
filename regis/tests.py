from django.test import TestCase, Client

from regis.models import Applicant

class RegistrationTestCase(TestCase):

    def setUp(self):
        self.regis_full_data_natid = {
            'has_national_id': '1',
            'national_id': '1234567890121',
            'national_id_confirm': '1234567890121',
            'passport_number': '',
            'passport_number_confirm': '',
            'email': 'test@test.com',
            'email_confirm': 'test@test.com',
            'prefix': 'นาย',
            'first_name': 'ทดสอบ',
            'last_name': 'มาก',
            'password': 'testpass1234',
            'password_confirm': 'testpass1234',
        }
    
    def test_register_index(self):
        response = self.client.get('/regis/register/')
        self.assertEqual(response.status_code, 200)


    def test_register_with_nat_id(self):
        response = self.client.post('/regis/register/',
                                    self.regis_full_data_natid)
        self.assertRedirects(response, '/')

        a = Applicant.objects.get(national_id=self.regis_full_data_natid['national_id'])
        self.assertIsNotNone(a)

        
    def test_register_with_bad_confirm_nat_id(self):
        data = self.regis_full_data_natid.copy()
        data['national_id_confirm'] = '0000000000000'
        response = self.client.post('/regis/register/',
                                    data)
        self.assertFormError(response,'form','national_id_confirm','รหัสประจำตัวประชาชนที่ยืนยันไม่ตรงกัน')

