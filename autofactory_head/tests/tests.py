import datetime

from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from packing.models import MarkingOperation
from catalogs.models import Line, Product

User = get_user_model()


class InterfaceTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='TestUser', password='1234567')
        self.client.login(username='TestUser', password='1234567')

        self.line = Line.objects.create(name='test_line')

    def test_marking_pages(self):
        """ Тестируются  страницы маркировки с фильтрами"""

        marking_data = {'production_date': datetime.datetime.today(),
                        'batch_number': 1,
                        'author': self.user,
                        'line': self.line}
        marking_operation = MarkingOperation.objects.create(**marking_data)

        response = self.client.get(reverse('marking'))
        data = response.context_data['data']
        self.assertEquals(response.status_code, 200)
        self.assertTrue(len(data))

        response = self.client.get(reverse('marking_operation_edit', kwargs={'pk': marking_operation.guid}))
        self.assertEquals(response.status_code, 200)

        response = self.client.get(reverse('marking_detail', kwargs={'pk': marking_operation.guid}))
        self.assertEquals(response.status_code, 200)

        response = self.client.get(reverse('marking'), data={'batch_number': 2})
        data = response.context_data['data']
        self.assertEquals(response.status_code, 200)
        self.assertFalse(len(data))

    def test_common_pages(self):
        response = self.client.get(reverse('index'), format='json')
        self.assertEquals(response.status_code, 200)
