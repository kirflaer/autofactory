from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import transaction

from catalogs.models import ExternalSource, Product
from tasks.models import TaskStatus
from tasks.task_services import RouterContent
from warehouse_management.models import MovementOperation, Pallet, BaseOperation, OperationPallet, OperationProduct, \
    PalletContent, PalletStatus, PalletCollectOperation
from warehouse_management.serializers import MovementOperationReadSerializer, MovementOperationWriteSerializer, \
    PalletCollectOperationWriteSerializer

User = get_user_model()


def get_content_router() -> dict[str: RouterContent]:
    """ Возвращает роутер для потомков Task.
    В зависимости от переданного типа задания формируется класс и сериализаторы"""

    return {'PRODUCT_MOVEMENT': RouterContent(task=MovementOperation,
                                              create_function=create_movement_operation,
                                              read_serializer=MovementOperationReadSerializer,
                                              write_serializer=MovementOperationWriteSerializer),
            'PALLET_COLLECT': RouterContent(task=PalletCollectOperation,
                                            create_function=create_collect_operation,
                                            read_serializer=PalletCollectOperationWriteSerializer,
                                            write_serializer=PalletCollectOperationWriteSerializer)}


@transaction.atomic
def create_collect_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения"""
    result = []
    for element in serializer_data:
        operation = PalletCollectOperation.objects.create(ready_to_unload=True, closed=True, status=TaskStatus.CLOSE,
                                                          user=user)
        pallets = create_pallets(element['pallets'])
        fill_operation_pallets(operation, pallets)
        result.append(operation.guid)
    return result


@transaction.atomic
def create_movement_operation(serializer_data: Iterable[dict[str: str]], user: User) -> Iterable[str]:
    """ Создает операцию перемещения. Возвращает идентификаторы внешнего источника """

    result = []
    for element in serializer_data:
        external_source = get_or_create_external_source(element)
        result.append(external_source.external_key)
        operation = MovementOperation.objects.filter(external_source=external_source).first()
        if operation is not None:
            continue
        operation = MovementOperation.objects.create(external_source=external_source)
        fill_operation_pallets(operation, element['pallets'])
        fill_operation_products(operation, element['products'])

    return result


def fill_operation_products(operation: BaseOperation, raw_data: Iterable[dict[str: str]]) -> None:
    """ Заполняет товары абстрактной операции """

    for task_product in raw_data:
        product = Product.objects.filter(external_key=task_product['product']).first()
        if product is None:
            continue

        weight = 0 if task_product.get('weight') is None else task_product['weight']
        count = 0 if task_product.get('count') is None else task_product['count']
        operation_products = OperationProduct.objects.create(product=product, weight=weight, count=count)
        operation_products.fill_properties(operation)


def fill_operation_pallets(operation: BaseOperation, raw_data: Iterable[str]) -> None:
    """ Заполняет информацию о паллетах абстрактной операции """

    for pallet_id in raw_data:
        pallet = Pallet.objects.filter(id=pallet_id).first()
        if pallet is None:
            continue
        operation_pallets = OperationPallet.objects.create(pallet=pallet)
        operation_pallets.fill_properties(operation)


def get_or_create_external_source(raw_data=dict[str: str]) -> ExternalSource:
    """ Создает либо находит элемент таблицы внешнего источника """

    external_source = ExternalSource.objects.filter(
        external_key=raw_data['external_source']['external_key']).first()
    if external_source is None:
        external_source = ExternalSource.objects.create(**raw_data['external_source'])
    return external_source


@transaction.atomic
def create_pallets(serializer_data: Iterable[dict[str: str]]) -> Iterable[str]:
    """ Создает паллету и наполняет ее кодами агрегации"""
    result = []

    for element in serializer_data:
        product = Product.objects.filter(guid=element['product']).first()
        pallet = Pallet.objects.filter(id=element['id'], product=product).first()
        if not pallet:
            product = element['product']
            element['product'] = Product.objects.filter(guid=product).first()
            serializer_keys = set(element.keys())
            serializer_keys.remove('codes')
            class_keys = set(dir(Pallet))
            fields = {key: element[key] for key in (class_keys & serializer_keys)}
            pallet = Pallet.objects.create(**fields, status=PalletStatus.CONFIRMED)

            for code in element['codes']:
                if not PalletContent.objects.filter(pallet=pallet, aggregation_code=code).exists():
                    PalletContent.objects.create(pallet=pallet, aggregation_code=code)
        result.append(pallet.id)
    return result
