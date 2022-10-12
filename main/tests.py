from django.test import SimpleTestCase


class MainTestCase(SimpleTestCase):

    def test_index(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
