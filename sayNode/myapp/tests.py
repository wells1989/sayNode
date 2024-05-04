from django.test import TestCase, Client
import json
from django.contrib.auth import get_user_model
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

        response_data = response.json()
        self.assertIn('sum', response_data)
        self.assertEqual(response_data['sum'], 15)


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

    def test_registration_valid(self):

        registration_data = {
            'username': 'test_user2',
            'email': 'test2@gmail.com',
            'password1': 'test_password2',
            'password2': 'test_password2',
        }

        response = self.client.post(self.url, data=registration_data)

        # checking status code
        self.assertEqual(response.status_code, 204)

        # checking 'sessionid' is in the response cookies
        self.assertIn('sessionid', response.cookies)

        # checking if  user with the specified username exists
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
            'username': 'test_user2',
            'email': 'test2@gmail.com',
            'password2': 'test_password',
        }

        response = self.client.post(self.url, data=registration_data)

        self.assertEqual(response.status_code, 400)

        self.assertNotIn('sessionid', response.cookies)

        response_data = response.json()

        error_message = response_data['password1']
        self.assertEqual(error_message, ["This field is required."])

        self.assertFalse(User.objects.filter(username='test_user2').exists())


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

    def test_logout(self):
        # authenticating the user
        login_data = {
            'username': self.user.username,
            'password': 'test_password'
        }

        login_response = self.client.post(self.login_url, login_data)
        self.assertEqual(login_response.status_code, 200)

        # Performing logout action
        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, 200)

        cookie_details = str(response.cookies.get("sessionid")).split(";")

        sessionid = cookie_details[0].split('=')[1].strip('"')
        expires = cookie_details[1].split("=")[1]

        expiration_date_formatted = datetime.datetime.strptime(expires, '%a, %d %b %Y %H:%M:%S %Z')
        current_time = datetime.datetime.utcnow()
        
        # DEV ONLY
        print(sessionid)
        print(expiration_date_formatted)
        print(current_time)

        # Asserting that sessionid is either absent or an empty string
        self.assertTrue(sessionid == "" or sessionid is None)

        # asserting that expiration date is before current_time, i.e. cookie has expired
        self.assertLess(expiration_date_formatted, current_time)
        
        # self.assertNotIn('sessionid', response.cookies) - doesn't work as is in response headers under Set-Cookie, not cookies section of postman

        response_data = response.json()

        logout_message = response_data['detail']
        self.assertEqual(logout_message, "Successfully logged out.")


