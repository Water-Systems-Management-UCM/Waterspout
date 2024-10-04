from django.contrib.auth.models import User, Group, AbstractUser
from django.core import mail
from rest_framework.test import APITestCase, APIRequestFactory
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from django.urls import reverse

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Waterspout.settings")

import django
django.setup()


class PasswordResetTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

        self.new_user = User()
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

    def extract_reset_link(self, email_body):
        import re
        match = re.search(r'http[s]?://[^\s]+', email_body)
        if match:
            return match.group(0)
        return None

    def extract_pk_token(self, reset_link):
        import re
        match = re.search(r'[?&]encoded_pk=(?P<encoded_pk>[0-9A-Za-z_\-]+)&token=(?P<token>[0-9A-Za-z\-]+)', reset_link)
        if match:
            return match.group('encoded_pk'), match.group('token')
        return None, None

    def get_reset_link(self):
        # Trigger the password reset email
        res = self.client.post(self.password_link, {'email': self.new_user.email})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Verify that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        mail.get_connection()

        # Extract the password reset link from the email content
        reset_link = self.extract_reset_link(email.alternatives[0][0])

        return reset_link

    def tearDown(self):
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

    def test_bad_token(self):
        reset_link = self.get_reset_link()
        # Check for pk and token
        pk, token = self.extract_pk_token(reset_link)
        token = token[::-1]  # reversing token to test for bad token
        self.assertIn('pk', reset_link)
        self.assertIn('token', reset_link)

        res = self.client.post(reset_link, {"password": "new_pass"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_bad_pk(self):
        reset_link = self.get_reset_link()

        # Check for pk and token
        pk, token = self.extract_pk_token(reset_link)
        pk = pk[::-1]  # reversing pk to test for bad pk
        self.assertIn('pk', reset_link)
        self.assertIn('token', reset_link)

        res = self.client.post(reset_link, {"password": "new_pass"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_password_reset(self):
        reset_link = self.get_reset_link()

        # Check for pk and token
        pk, token = self.extract_pk_token(reset_link)
        self.assertIn('pk', reset_link)
        self.assertIn('token', reset_link)

        new_password = "different-pass"

        reset_url = reverse('password-reset') + f'?encoded_pk={pk}&token={token}'

        reset_url = "http://localhost:5173" + reset_url

        reset_response = self.client.patch(reset_url, {
            'password': new_password,
            'encoded_pk': pk,
            'token': token
        })

        self.assertEqual(reset_response.status_code, status.HTTP_200_OK)

        login = self.client.login(username=self.new_user.username, password=self.new_user.password)
        self.assertFalse(login)

        login = self.client.login(username=self.new_user.username, password=new_password)
        self.assertTrue(login)

    def test_password_change(self):
        # new user has no permissions, but is authenticated
        login = self.client.login(username=self.new_user.username, password="testpassword123")
        self.client.force_authenticate(user=self.new_user)  # set the authentication - no tokens needed
        res = self.client.patch(self.password_change, {'password': "new_pass"})  # changing password

        # Signing in with new password after change
        login = self.client.login(username=self.new_user.username, password="new_pass")
        self.assertTrue(login)

        # Testing old password to make sure it has been updated
        login = self.client.login(username=self.new_user.username, password="testpassword123")
        self.assertFalse(login)

    def test_password_reset_w_different_token(self):
        reset_link = self.get_reset_link()

        pk, token = self.extract_pk_token(reset_link)
        self.assertIn('encoded_pk', reset_link)
        self.assertIn('token', reset_link)

        new_password = "different-pass"

        different_user = User.objects.create_user(
            username='testuser2',
            email='testuser2@example.com',
            password='testpassword123',
        )
        different_user.save()

        # Generate a new token for the different user
        diff_token = default_token_generator.make_token(different_user)

        reset_url = reverse('password-reset') + f'?encoded_pk={pk}&token={diff_token}'

        reset_response = self.client.patch(reset_url, {
            'password': new_password,
            'encoded_pk': pk,
            'token': diff_token
        })

        self.assertEqual(reset_response.status_code, status.HTTP_400_BAD_REQUEST)

