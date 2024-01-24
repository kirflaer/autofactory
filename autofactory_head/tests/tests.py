import csv
import datetime
import os
import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework.response import Response

from factory_core.models import Shift, TypeShift
from packing.models import MarkingOperation, MarkingOperationMark
from catalogs.models import Line, Product

User = get_user_model()


class BaseClassTest(APITestCase):
    def setUp(self) -> None:
        self.line = Line.objects.create(name='test_line')
        self.user = User.objects.create_user(username='TestUser', password='1234567', line=self.line)
        self.client.login(username='TestUser', password='1234567')
        self.product_weight = Product.objects.create(name='test_weight',
                                                     gtin='4610046202380',
                                                     external_key=str(uuid.uuid4()),
                                                     expiration_date=10,
                                                     is_weight=True)
        self.product_non_weight = Product.objects.create(name='test_non_weight',
                                                         gtin='4607104080790',
                                                         external_key=str(uuid.uuid4()),
                                                         expiration_date=20)


class InterfaceTests(BaseClassTest):

    def test_marking_pages(self):
        """ Тестируются страницы маркировки с фильтрами"""

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


class MarkingTestCase(BaseClassTest):
    def setUp(self):
        super().setUp()

        self.products = [self.product_weight, self.product_non_weight]
        self.shift = Shift.objects.create(
            line=self.line,
            batch_number='123',
            production_date=datetime.datetime.utcnow(),
            type=TypeShift.MARKED,
            author=self.user,
        )

    def test_create_marking_operation(self):
        # Выполняем запрос к API для создания маркировки
        for product in self.products:
            response = self.create_marking_operation(product)
            self.assertEqual(response.status_code, 201)  # Ожидаем успешный код ответа

        # Проверяем, что задания маркировки были созданы
        self.assertEqual(MarkingOperation.objects.count(), len(self.products))

        product_ids = frozenset(product.guid for product in self.products)

        # Проверяем создание операции маркировки для каждого товара из списка
        marking_operations = MarkingOperation.objects.all()
        for marking_operation in marking_operations:
            self.assertEqual(marking_operation.shift, self.shift)
            self.assertEqual(marking_operation.line, self.user.line)
            self.assertIn(marking_operation.product.guid, product_ids)

    def test_close_marking_operation(self):

        marks_by_gtin = group_marks_by_gtin(list(product.gtin for product in self.products))
        marking_operations_ids = []
        marks_count = 0
        for product in self.products:
            marking_operation = self.create_marking_operation(product).data
            marking_operations_ids.append(marking_operation['guid'])
            url = f'/api/v4/marking/{marking_operation["guid"]}/'

            marks = marks_by_gtin[product.gtin]
            marks_count += len(marks)

            payload = [
                {
                    'aggregation_code': '-',
                    'marks': [
                        {
                            'mark': mark,
                            'scan_date': timezone.make_aware(datetime.datetime.utcnow())
                        }
                        for mark in marks
                    ],
                    'product': product.guid,
                }
            ]
            response = self.client.put(url, payload, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(MarkingOperationMark.objects.count(), marks_count)

        # Закрываем смену
        payload = {
            'closed': True,
            'products': []
        }
        response = self.client.patch(f'/api/v4/shifts/{self.shift.guid}/', payload, format='json')
        self.assertEqual(response.status_code, 200)

        # Проверяем все флаги маркировки после закрытия
        marking_operations = MarkingOperation.objects.filter(guid__in=marking_operations_ids)
        for marking_operation in marking_operations:
            self.assertTrue(marking_operation.closed)
            self.assertTrue(marking_operation.ready_to_unload)

    def create_marking_operation(self, product: Product) -> Response:
        payload = {
            'line': self.line.guid,
            'product': product.guid,
            'shift': self.shift.guid,
            'production_date': str(self.shift.production_date.strftime('%Y-%m-%d')),
            'batch_number': self.shift.batch_number
        }
        return self.client.post('/api/v4/marking/', payload, format='json')


def group_marks_by_gtin(product_gtins: list[str]) -> dict[str, list[str]]:
    marks_by_gtin = {gtin: [] for gtin in product_gtins}

    with open(os.path.join(os.path.dirname(__file__), 'marks.csv'), 'r') as file:
        marks_reader = csv.reader(file)
        for row in marks_reader:
            mark = row[0]

            for gtin in product_gtins:
                if mark.startswith(f'010{gtin}'):
                    marks_by_gtin[gtin].append(mark)
                    break

    return marks_by_gtin
