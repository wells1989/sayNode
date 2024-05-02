from django.test import TestCase, Client
import json

class SumIntegersViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_sum_integers_with_valid_data(self):
        
        data = {'int_1': 5, 'int_2': 10}
        json_data = json.dumps(data)

        response = self.client.post('/sum_integers/', data=json_data, content_type='application/json')

        # assertion checks
        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertIn('sum', response_data)
        self.assertEqual(response_data['sum'], 15)


    def test_sum_integers_with_invalid_data(self):

        data = {'int_1': 'a', 'int_2': 'b'}
        json_data = json.dumps(data)

        response = self.client.post('/sum_integers/', data=json_data, content_type='application/json')

        # assertion checks
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertEqual(response_data['error'], 'Please provide valid integers for num1 and num2')
