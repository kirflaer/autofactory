import csv
import datetime
import os
import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework.response import Response

from catalogs.models import Line, Product
from factory_core.models import Shift, TypeShift
from packing.models import MarkingOperation, MarkingOperationMark
from tasks.models import TaskStatus
from warehouse_management.models import PalletCollectOperation, Pallet, OperationPallet

User = get_user_model()


class BaseClassTest(APITestCase):
    def setUp(self) -> None:
        self.api_version = '4'
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


class PalletCollectTestCase(BaseClassTest):

    def setUp(self):
        super().setUp()

        self.pallets = []
        counter = 0
        for type_shift in TypeShift:
            Pallet.objects.create(
                id=f'01046071040807071323072991p-c46{counter}',
                shift=Shift.objects.create(
                    line=self.line,
                    batch_number=f'12{counter}',
                    production_date=datetime.datetime.utcnow(),
                    type=type_shift,
                    author=self.user
                )
            )
            counter += 1

    def create_pallet_collect_operation(self):
        for pallet in self.pallets:
            payload = {
                'pallets': [{
                    'content_count': 5,
                    'id': pallet.id,
                    'batch_number': pallet.shift.batch_number,
                    'product': self.product_weight.guid,
                    'production_date': pallet.shift.production_date.strftime('%Y-%m-%d'),
                    'shift': pallet.shift.guid,
                }],
                'shift': pallet.shift.guid,
            }
            response = self.client.post('/api/v4/tasks/pallet_collect/', payload, format='json')
            # Не корректный ответ на POST запрос возвращает статус 200
            self.assertEqual(response.status_code, 200)

    def test_pallet_collect_operation(self):

        self.create_pallet_collect_operation()

        operations_pallet = OperationPallet.objects.all()
        for operation in operations_pallet:
            self.assertIn(operation.pallet.shift.type, TypeShift)  # Не проставляется смена в pallet

            response = self.client.patch(
                f'/api/v4/pallets/{operation.pallet.guid}/',
                {'status': 'CONFIRMED'},
                format='json'
            )
            self.assertEqual(response.status_code, 200)
            operation.pallet.refresh_from_db()
            self.assertEqual(operation.pallet.status, 'CONFIRMED')
            # Закрываем смену
            payload = {
                'closed': True,
                'products': []
            }
            response = self.client.patch(f'/api/v4/shifts/{operation.pallet.shift.guid}/', payload, format='json')
            self.assertEqual(response.status_code, 200)

        pallet_collect_operation = PalletCollectOperation.objects.all()
        for pallet_collect in pallet_collect_operation:
            self.assertEqual(pallet_collect.status, TaskStatus.CLOSE)
            self.assertTrue(pallet_collect.closed)
            self.assertTrue(pallet_collect.ready_to_unload)
