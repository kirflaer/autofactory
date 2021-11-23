import datetime
from .models import (
    RawMark,
    MarkingOperation,
    MarkingOperationMark,
    CollectingOperation,
    CollectCode
)
from catalogs.models import Product
from collections.abc import Iterable
from typing import Optional
import base64
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


def create_collect_operation(author: User, collecting_data: Iterable) -> None:
    for element in collecting_data:
        operation = CollectingOperation.objects.create(author=author,
                                                       identifier=element[
                                                           'identifier'])
        for code in element['codes']:
            CollectCode.objects.create(operation=operation, code=code)


def confirm_marks_unloading(operations: list) -> None:
    """Устанавливает признак unloaded у операций маркировок
    Подтверждая выгрузку во внешнюю систему"""
    for guid in operations:
        operation = MarkingOperation.objects.get(guid=guid)
        operation.unloaded = True
        operation.save()


def get_marks_to_unload() -> list:
    """ Возвращает список марок для выгрузки. Марки по закрытым маркировкам
    С отметкой ready_to_unload"""

    values = MarkingOperationMark.objects.filter(
        operation__ready_to_unload=True,
        operation__unloaded=False,
        operation__closed=True,
    ).values('encoded_mark',
             'product__external_key',
             'operation__production_date',
             'operation__batch_number',
             'operation__guid',
             'operation__organization__external_key',
             'operation__line',
             'operation__line__storage__external_key',
             'operation__line__department__external_key',
             'operation__line__type_factory_operation__external_key',
             )

    data = []
    for value in values:
        element = {'operation': value['operation__guid'],
                   'encoded_mark': value['encoded_mark'],
                   'product': value['product__external_key'],
                   'production_date': value[
                       'operation__production_date'].strftime(
                       "%d.%m.%Y"),
                   'batch_number': value['operation__batch_number'],
                   'organization': value[
                       'operation__organization__external_key'],
                   'storage': value[
                       'operation__line__storage__external_key'],
                   'line': value[
                       'operation__line'],
                   'department': value[
                       'operation__line__department__external_key'],
                   'type_factory_operation': value[
                       'operation__line__type_factory_operation__external_key']
                   }
        data.append(element)

    return data


def remove_marks(marks: list) -> None:
    """Ищет марки за последние три дня для невыгруженных операций маркировки
    если такие марки найдены она их удаляет"""
    for mark in marks:
        indexes_to_remove = []
        date_filter = datetime.datetime.now() - datetime.timedelta(7)
        for element in MarkingOperationMark.objects.filter(
                operation__date__gte=date_filter, operation__unloaded=False,
                mark=mark):
            indexes_to_remove.append(element.id)

        for index in indexes_to_remove:
            MarkingOperationMark.objects.get(pk=index).delete()


def register_to_exchange(operation: MarkingOperation) -> bool:
    """Регистрирует к обмену операцию маркировки если есть возможность
    Возвращает Истина в случае если операция зарегистрирована к обмену"""

    start_date = datetime.datetime.now()
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = datetime.datetime.now()
    end_date = end_date.replace(hour=23, minute=59, second=59)
    markings = MarkingOperation.objects.filter(
        date__range=[start_date, end_date]).filter(unloaded=False).filter(
        ready_to_unload=False)

    settings = operation.author.settings
    need_exchange = True
    if settings.type_marking_close == settings.ALL_IN_DAY_BY_LINE:
        markings = markings.filter(line=operation.line)
    elif settings.type_marking_close == settings.ALL_IN_DAY_BY_BAT_NUMBER:
        markings = markings.filter(batch_number=operation.batch_number)
    elif (settings.type_marking_close ==
          settings.ALL_IN_DAY_BY_LINE_BY_BAT_NUMBER):
        markings = markings.filter(line=operation.line,
                                   batch_number=operation.batch_number)

    for marking in markings:
        if marking != operation and not marking.closed:
            need_exchange = False
            break

    if need_exchange:
        for uuid in markings.values_list("guid", flat=True):
            marking = MarkingOperation.objects.get(guid=uuid)
            marking.ready_to_unload = True
            marking.save()
        operation.ready_to_unload = True
        operation.save()

    return need_exchange


def clear_raw_marks(operation: MarkingOperation) -> None:
    """Очищает данные сырых марок
    после создание экземпляров MarkingOperationMark"""
    if RawMark.objects.filter(operation=operation).exists():
        RawMark.objects.filter(operation=operation).delete()


def get_product_gtin_from_mark(mark: str) -> Optional[int]:
    if len(mark) >= 16:
        return int(mark[2:16])
    else:
        return None


def marking_close(operation: MarkingOperation, data: Iterable) -> None:
    """Закрывает операцию маркировки, марки берет либо из запроса закрытия
    либо из сырых марок полученных из автоматического сканера"""
    with transaction.atomic():
        create_marking_marks(operation, data)
        register_to_exchange(operation)
        operation.close()
        if operation.author.role == User.VISION_OPERATOR:
            clear_raw_marks(operation)


def create_marking_marks(operation: MarkingOperation, data: Iterable) -> None:
    """Создает и записывает в базу экземпляры MarkingOperationMark"""
    products = {}
    marking_marks_instances = []
    marks = []

    for value in data:
        if not isinstance(value, dict):
            continue

        mark = value.get('mark')
        if mark is None:
            guid = value.get('product')
            product = products.get(guid)
            if product is None:
                product = _get_product(guid=guid)
                products[guid] = product

            value['product'] = product
            _create_instance_marking_marks(
                marking_marks_instances=marking_marks_instances,
                operation=operation, **value)
        else:
            if marks.count(mark):
                continue

            marks.append(mark)
            gtin = get_product_gtin_from_mark(mark)
            product = products.get(gtin)
            if product is None:
                product = _get_product(gtin=gtin)
                products[gtin] = product

            _create_instance_marking_marks(
                marking_marks_instances,
                operation,
                product,
                None,
                marks=(mark,))

    MarkingOperationMark.objects.bulk_create(marking_marks_instances)


def get_base64_string(source: str) -> str:
    data_bytes = source.encode("utf-8")
    base64_bytes = base64.b64encode(data_bytes)
    base64_string = base64_bytes.decode("utf-8")
    return base64_string


def _get_product(gtin: Optional[int] = None,
                 guid: Optional[str] = None) -> Optional[Product]:
    """Поиск номенклатуры по марке либо по GUID"""
    product_filter = {}
    if guid is None:
        product_filter['gtin'] = gtin
    else:
        product_filter['guid'] = guid

    if Product.objects.filter(**product_filter).exists():
        return Product.objects.filter(**product_filter).first()
    else:
        return None


def _create_instance_marking_marks(marking_marks_instances: Iterable,
                                   operation: MarkingOperation,
                                   product: Optional[Product],
                                   aggregation_code: Optional[str],
                                   marks: Iterable) -> None:
    """Создает экземпляры модели MarkingOperationMark
    сырые марки кодируются в base64
    Экземпляры добавляются в массив marking_operation_marks
    Для использования конструкции bulk_create
    """

    for mark in marks:
        marking_marks_instances.append(
            MarkingOperationMark(operation=operation,
                                 mark=mark,
                                 encoded_mark=get_base64_string(mark),
                                 product=product,
                                 aggregation_code=aggregation_code))
