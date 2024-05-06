from django.test import TestCase, Client
import json
from django.contrib.auth import get_user_model, authenticate
import datetime

User = get_user_model()


class SumIntegersViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/sum_integers/'

    def test_sum_integers_with_valid_data(self):
        
        data = {'int_1': 5, 'int_2': 10}
        json_data = json.dumps(data)

        response = self.client.post(self.url, data=json_data, content_type='application/json')

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response['Content-Type'], 'application/json')

        response_data = response.json()
        self.assertIn('sum', response_data)
        self.assertEqual(response_data['sum'], 15)
        self.assertIsInstance(response_data['sum'], int)


    def test_sum_integers_with_invalid_data(self):

        data = {'int_1': 'a', 'int_2': 'b'}
        json_data = json.dumps(data)

        response = self.client.post(self.url, data=json_data, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Please provide valid integers for num1 and num2')

    def test_sum_integers_with_missing_data(self):

        data = {}
        json_data = json.dumps(data)

        response = self.client.post(self.url, data=json_data, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Please provide valid integers for num1 and num2')


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/dj-rest-auth/registration/'

        self.user = get_user_model().objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )

        self.registration_data = {
            'username': 'test_user2',
            'email': 'test2@gmail.com',
            'password1': 'test_password2',
            'password2': 'test_password2',
        }

    def test_registration_valid(self):

        response = self.client.post(self.url, data=self.registration_data)

        # checking status code
        self.assertEqual(response.status_code, 204)

        # checking 'sessionid' is in the response cookies
        self.assertIn('sessionid', response.cookies)

        # checking if user with the specified username exists
        self.assertTrue(User.objects.filter(username='test_user2').exists())

    def test_registration_duplicate(self):
        user = self.user

        registration_data = {
            'username': user.username,
            'email': user.email,
            'password1': 'test_password2',
            'password2': 'test_password2'
        }

        response = self.client.post(self.url, data=registration_data)

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('sessionid', response.cookies)

        response_data = response.json()

        username_errors = response_data['username']
        self.assertEqual(username_errors, ["A user with that username already exists."])

    def test_registration_missing_info(self):

        registration_data = {
            'username': self.registration_data["username"],
            'email': self.registration_data["email"],
            'password2': 'test_password',
        }

        response = self.client.post(self.url, data=registration_data)

        self.assertEqual(response.status_code, 400)

        self.assertNotIn('sessionid', response.cookies)

        response_data = response.json()

        error_message = response_data['password1']
        self.assertEqual(error_message, ["This field is required."])

        self.assertFalse(User.objects.filter(username='test_user2').exists())

    def test_registration_short_password(self):

        registration_data = {
            'username': self.registration_data["username"],
            'email': self.registration_data["email"],
            'password1': 'test',
            'password2': 'test',
        }

        response = self.client.post(self.url, data=registration_data)

        self.assertEqual(response.status_code, 400)

        self.assertNotIn('sessionid', response.cookies)

        response_data = response.json()

        error_message = response_data['password1']
        self.assertIn("This password is too short. It must contain at least 8 characters.", error_message)

    def test_registration_invalid_email(self):

        registration_data = {
            'username': self.registration_data["username"],
            'email': 'test2',
            'password1': 'test_user2',
            'password2': 'test_user2',
        }

        response = self.client.post(self.url, data=registration_data)

        self.assertEqual(response.status_code, 400)

        self.assertNotIn('sessionid', response.cookies)

        response_data = response.json()

        error_message = response_data['email']
        self.assertEqual(error_message, ["Enter a valid email address."])


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/dj-rest-auth/login/'

        self.user = get_user_model().objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )

    def test_successful_login(self):
        login_data = {
            'username': self.user.username,
            'email': self.user.email,
            'password': 'test_password' # not self.user.password as that's the hashed stored version
        }

        response = self.client.post(self.url, data=login_data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('sessionid', response.cookies)

        response_data = response.json()

        key_value = response_data['key']
        self.assertTrue(len(key_value) > 10)

    def test_unsuccessful_login(self):
        login_data = {
            'username': self.user.username,
            'email': self.user.email,
            'password': 'wrong_password'
        }

        response = self.client.post(self.url, data=login_data)

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('sessionid', response.cookies)

        response_data = response.json()

        login_error = response_data['non_field_errors']
        self.assertEqual(login_error, ["Unable to log in with provided credentials."])

    def test_non_existent_user_login(self):
        login_data = {
            'username': "non_existent_user",
            'email': "doesn't_exist@gmail.com",
            'password': 'non_existent'
        }

        response = self.client.post(self.url, data=login_data)

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('sessionid', response.cookies)

        response_data = response.json()

        login_error = response_data['non_field_errors']
        self.assertEqual(login_error, ["Unable to log in with provided credentials."])


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = '/dj-rest-auth/login/'
        self.logout_url = '/dj-rest-auth/logout/'

        self.user = get_user_model().objects.create_user(
            username='test_user',
            email='test@example.com',
            password='test_password'
        )

    def test_logout_authenticated_user(self):
        # authenticating / logging in the user
        user = authenticate(username=self.user.username, password='test_password')

        self.client.force_login(user)

        # Performing logout action
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, 200)

        cookie_details = str(response.cookies.get("sessionid")).split(";")

        # checking the sessionid has been removed and is expired
        sessionid = cookie_details[0].split('=')[1].strip('"')
        expires = cookie_details[1].split("=")[1]

        expiration_date_formatted = datetime.datetime.strptime(expires, '%a, %d %b %Y %H:%M:%S %Z')
        current_time = datetime.datetime.utcnow()

        # Asserting that sessionid is either absent or an empty string
        self.assertTrue(sessionid == "" or sessionid is None)

        # asserting that expiration date is expired or none
        self.assertTrue(expiration_date_formatted < current_time or expiration_date_formatted is None)

        response_data = response.json()

        logout_message = response_data['detail']
        self.assertEqual(logout_message, "Successfully logged out.")

    def test_logout_unauthenticated_user(self):
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, 200)

        # Check if the session is still empty
        session = self.client.session
        self.assertFalse(session.has_key('_auth_user_id'))

        response_data = response.json()
        self.assertEqual(response_data['detail'], "Successfully logged out.")
