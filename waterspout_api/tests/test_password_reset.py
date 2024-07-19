from django.contrib.auth.models import User, Group, AbstractUser
from django.core import mail
from rest_framework.test import APITestCase, APIRequestFactory
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from django.urls import reverse

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

import django
django.setup()


class PasswordResetTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.new_user = User()
        # self.new_user.email = "micaheltapia000@gmail.com"
        # self.new_user.username = "test_email"
        # self.new_user.password = "new_pass"
        self.new_user = User.objects.create_user(
            username='testuser',
            email='micaheltapia000@gmail.com',
            password='testpassword123',
            first_name='Test',
            last_name='User',
        )

        self.new_user.save()

        self.password_link = reverse('password-reset-link')
        self.password_link_reset = reverse('password-reset')
        self.password_change = reverse('password-change')

        self.user_data = {
            'email': '<EMAIL>',
            'password': '<PASSWORD>',
        }

    def tearDown(self):
        # self.user.delete()
        return super().tearDown()

    def test_password_reset_get_link_email_not_found(self):
        data = {
            'email': 'not_reg@gmail.com'
        }
        res = self.client.post(self.password_link, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_get_link_email(self):
        res = self.client.post(self.password_link, {'email': self.new_user.email})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def extract_reset_link(self, email_body):
        # Implement the logic to extract the reset link from the email body
        # This will depend on the exact format of the email
        import re
        match = re.search(r'http[s]?://[^\s]+', email_body)
        if match:
            return match.group(0)
        return None

    def extract_pk_token(self, reset_link):
        # Implement the logic to extract the uid and token from the reset link
        # Typically the link is something like: /reset/MQ/token/
        import re
        match = re.search(r'/password-reset#(?P<encoded_pk>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/',
                          reset_link)
        if match:
            return match.group('encoded_pk'), match.group('token')
        return None, None

    def test_password_reset(self):
        # Trigger the password reset email
        res = self.client.post(self.password_link, {'email': self.new_user.email})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        mail.get_connection()

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, 'Password Reset Request')
        #
        # # Extract the password reset link from the email content
        # reset_link = self.extract_reset_link(email.body)
        #
        # # Verify that the link contains the pk and token
        # pk, token = self.extract_pk_token(reset_link)
        # self.assertIn('pk', reset_link)
        # self.assertIn('token', reset_link)
        #
        # new_password = "different-pass"
        #
        # res = self.client.post(self.password_link_reset, {
        #     'token': token,
        #     'encoded_pk': pk,
        #     "password": new_password
        # })
        #
        # self.assertEqual(res.status_code, status.HTTP_200_OK)
        #
        # login = self.client.login(username=self.new_user.username, password=new_password)
        # self.assertTrue(login)

    def test_password_change(self):
        # new user has no permissions, but is authenticated
        login = self.client.login(username=self.new_user.username, password="testpassword123")
        self.client.force_authenticate(user=self.new_user)  # set the authentication - no tokens needed
        res = self.client.post(self.password_change, {'password': "new_pass"})
        import pdb
        pdb.set_trace()
        login = self.client.login(username=self.new_user.username, password="new_pass")
        self.assertTrue(login)

        login = self.client.login(username=self.new_user.username, password="testpassword123")
        self.assertFalse(login)