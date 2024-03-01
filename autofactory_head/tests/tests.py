import csv
import datetime
import os
from typing import Any
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
from warehouse_management.models import (
    PalletCollectOperation,
    Pallet,
    OperationPallet,
    StorageCell,
    StorageArea,
    SelectionOperation,
    ShipmentOperation,
    TypeCollect,
)

User = get_user_model()


class BaseClassTest(APITestCase):

    def setUp(self) -> None:
        self.url_api = '/api/v4/tasks'
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

        self.pallets = tuple(
            Pallet.objects.create(
                id=f'01046071040807071323072991p-c46{i}',
                shift=Shift.objects.create(
                    line=self.line,
                    batch_number=f'12{i}',
                    production_date=datetime.datetime.utcnow(),
                    type=type_shift,
                    author=self.user
                )
            )
            for i, type_shift in enumerate(TypeShift, start=1)
        )

    def create_pallet_collect_operation(self):
        for pallet in self.pallets:
            payload = self._get_payload_data(pallet)
            response = self.client.post(f'{self.url_api}/pallet_collect/', payload, format='json')
            self.assertEqual(response.status_code, 201)

    def test_pallet_collect_operation(self):
        """ Тест PATCH запроса /tasks/pallet_collect """

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

    def _get_payload_data(self, pallet: Pallet) -> dict[str: Any]:

        return {
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


class ShipmentTestCase(BaseClassTest):

    def setUp(self):
        super().setUp()

        self.url_api = '/api/v4/tasks'

        self.pallets = tuple(
            Pallet.objects.create(
                id=f'01046071040807071323072991p-c46{i}',
                shift=Shift.objects.create(
                    line=self.line,
                    batch_number=f'12{i}',
                    production_date=datetime.datetime.utcnow(),
                    type=type_shift,
                    author=self.user
                )
            )
            for i, type_shift in enumerate(TypeShift, start=1)
        )
        self.cell = StorageCell.objects.create()

    def create_shipment(self, endpoint: str):
        payload = self._get_payload_data()
        response = self.client.post(f'{self.url_api}/{endpoint}/', payload, format='json')
        self.assertEqual(response.status_code, 201)

        return response

    def test_create_shipment_operation(self):
        """ Тест POST запроса /tasks/shipment """

        response = self.create_shipment('shipment_movement')
        self.assertEqual(response.data['type_task'], 'shipment_movement')

        response = self.create_shipment('shipment')
        self.assertEqual(response.data['type_task'], 'shipment')

    def test_fetch_shipment_operation_movement(self):
        """ Тест GET запроса /tasks/shipment_movement/ """

        self.create_shipment('shipment_movement')
        subtypes = self._get_subtype('shipment_movement')

        for _type in subtypes:
            self.assertEqual(_type, TypeCollect.MOVEMENT)

        response = self.client.get(
            f'{self.url_api}/shipment/',
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_fetch_shipment_operation(self):

        self.create_shipment('shipment')
        subtypes = self._get_subtype('shipment')

        for _type in subtypes:
            self.assertEqual(_type, TypeCollect.SHIPMENT)

        response = self.client.get(
            f'{self.url_api}/shipment_movement/',
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def _get_subtype(self, type_task: str):

        response = self.client.get(
            f'{self.url_api}/{type_task}/',
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(len(response.data), 0)

        selection_operation_ids = tuple(element['guid'] for element in response.data)
        return SelectionOperation.objects.filter(
            guid__in=selection_operation_ids
        ).values_list('subtype_task', flat=True)

    def _get_payload_data(self):

        return [
            {
                'external_source':
                    {
                        'name': 'Заявка на завод 0000-008562 от 18.04.2022 11:43:25',
                        'external_key': '9cac65ba-bef3-11ec-87f7-2e6094fbc090',
                        'number': '22',
                        'date': '2022-12-12+'
                    },
                'pallets':
                    [
                        {
                            'content_count': 5,
                            'id': pallet.id,
                            'batch_number': pallet.shift.batch_number,
                            'product': self.product_weight.guid,
                            'production_date': pallet.shift.production_date.strftime('%Y-%m-%d'),
                            'shift': pallet.shift.guid,
                        }
                        for pallet in self.pallets
                    ],
                'cells':
                    [
                        {
                            'cell': self.cell.guid,
                            'cell_destination': self.cell.guid,
                            'pallet': pallet.id
                        }
                        for pallet in self.pallets
                    ]
            }
        ]


class SelectionTestCase(BaseClassTest):

    def setUp(self):
        super().setUp()

        self.pallets = tuple(
            Pallet.objects.create(
                id=f'01046071040807071323072991p-c46{i}',
                shift=Shift.objects.create(
                    line=self.line,
                    batch_number=f'12{i}',
                    production_date=datetime.datetime.utcnow(),
                    type=type_shift,
                    author=self.user
                )
            )
            for i, type_shift in enumerate(TypeShift, start=1)
        )
        self.cell = StorageCell.objects.create(storage_area=StorageArea.objects.create(name='test'))

    def create_selection_operation(self, endpoint):
        payload = self._get_payload_data()
        response = self.client.post(f'{self.url_api}/{endpoint}/', payload, format='json')
        self.assertEqual(response.status_code, 201)

        return response

    def test_create_selection_operation(self):
        """ Тест POST запроса /tasks/selection """

        response = self.create_selection_operation('selection_movement')
        self.assertEqual(response.data['type_task'], 'selection_movement')

        response = self.create_selection_operation('selection')
        self.assertEqual(response.data['type_task'], 'selection')

    def test_fetch_selection_operation_movement(self):
        """ Тест GET запроса /tasks/selection_movement/ """

        self.create_selection_operation('selection_movement')
        subtypes = self._get_subtype('selection_movement')

        for _type in subtypes:
            self.assertEqual(_type, TypeCollect.MOVEMENT)

        response = self.client.get(
            f'{self.url_api}/selection/',
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_fetch_selection_operation(self):

        self.create_selection_operation('selection')
        subtypes = self._get_subtype('selection')

        for _type in subtypes:
            self.assertEqual(_type, TypeCollect.SELECTION)

        response = self.client.get(
            f'{self.url_api}/selection_movement/',
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def _get_subtype(self, type_task: str):

        response = self.client.get(
            f'{self.url_api}/{type_task}/',
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(len(response.data), 0)

        selection_operation_ids = tuple(element['guid'] for element in response.data)
        return SelectionOperation.objects.filter(
            guid__in=selection_operation_ids
        ).values_list('subtype_task', flat=True)

    def _get_payload_data(self):

        return [
            {
                'external_source':
                    {
                        'name': 'Заявка на завод 0000-008562 от 18.04.2022 11:43:25',
                        'external_key': '9cac65ba-bef3-11ec-87f7-2e6094fbc090',
                        'number': '22',
                        'date': '2022-12-12+'
                    },
                'cells':
                    [
                        {
                            'cell': self.cell.guid,
                            'cell_destination': self.cell.guid,
                            'pallet': pallet.id
                        }
                        for pallet in self.pallets
                    ]
            }
        ]
