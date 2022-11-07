import datetime
import json
import uuid
from typing import NamedTuple

from django.contrib.auth import get_user_model
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from packing.models import MarkingOperation
from catalogs.models import Line, Product

User = get_user_model()


class BaseClassTest(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username='TestUser', password='1234567')
        self.client.login(username='TestUser', password='1234567')
        self.line = Line.objects.create(name='test_line')
        self.product_simple = Product.objects.create(name='Сыр обычный',
                                                     gtin='4610046202380',
                                                     external_key=str(uuid.uuid4()),
                                                     expiration_date=10)
        self.product_weight = Product.objects.create(name='Сыр весовой',
                                                     gtin='4607104080790',
                                                     external_key=str(uuid.uuid4()),
                                                     expiration_date=20,
                                                     is_weight=True)


class InterfaceTests(BaseClassTest):

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
    """ Тест на открытие страницы дашборда """
    response = self.client.get(reverse('index'), format='json')
    self.assertEquals(response.status_code, 200)


class MarkingTests(BaseClassTest):
    def setUp(self) -> None:
        with open('./tests/marks.csv', 'r') as marks_file:
            self.marks = [line for line in marks_file.readlines()]

        super().setUp()

    def test_marking_online_v2(self):
        data = {
            'batch_number': '1111',
            'production_date': '2022-10-10',
            'line': self.line.guid,
            'group': str(uuid.uuid4()),
            'group_offline': '555'
        }
        # Открываем маркировку
        response = self.client.post('/api/v2/marking/', data=data)
        self.assertEquals(response.status_code, 201)

        marking_guid = response.data.get('guid')

        # Добавляем марки
        marks_data = [{
            'product': str(self.product_simple.guid),
            'marks': self.marks
        }]

        response = self.client.put(f'/api/v2/marking/{marking_guid}/', data=json.dumps(marks_data),
                                   content_type='application/json')
        dd = 33
