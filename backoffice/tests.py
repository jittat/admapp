# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase


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
