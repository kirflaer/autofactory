import datetime
from .models import RawMark, MarkingOperation, MarkingOperationMarks
from catalogs.models import Product
from collections.abc import Iterable
from typing import Union, Optional
from django.conf import settings
import base64


def add_marks(operation: MarkingOperation, marks: list) -> None:
    """Добавляет марки в выбранную операцию маркировки"""
    for mark in marks:
        product = _get_product(mark)
        _create_marking_operation(operation, product, None, (mark,))


def remove_marks(marks: list) -> None:
    """Ищет марки за последние три дня для невыгруженных операций маркировки
    если такие марки найдены она их удаляет"""
    for mark in marks:
        indexes_to_remove = []
        date_filter = datetime.datetime.now() - datetime.timedelta(7)
        for element in MarkingOperationMarks.objects.filter(
                operation__date__gte=date_filter, operation__unloaded=False,
                mark=mark):
            indexes_to_remove.append(element.id)

        for index in indexes_to_remove:
            MarkingOperationMarks.objects.get(pk=index).delete()


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

    need_exchange = True
    if settings.TYPE_MARKING_CLOSE == 'ALL_IN_DAY_BY_LINE':
        markings = markings.filter(line=operation.line)
    elif settings.TYPE_MARKING_CLOSE == 'ALL_IN_DAY_BY_BAT_NUMBER':
        markings = markings.filter(batch_number=operation.batch_number)
    elif settings.TYPE_MARKING_CLOSE == 'ALL_IN_DAY_BY_LINE_BY_BAT_NUMBER':
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


def marking_close(operation: MarkingOperation, data: Iterable) -> None:
    """Закрывает операцию маркировки, марки берет либо из запроса закрытия
    либо из сырых марок полученных из автоматического сканера"""
    products = {}
    marking_operations = []

    for value in data:
        if not isinstance(value, dict):
            continue

        mark = value.get('mark')
        if mark is None:
            pass
            guid = value.get('product')
            product = products.get(guid)
            if product is None:
                product = _get_product(guid=guid)
                products[guid] = product

            value['product'] = product
            _create_marking_operation(operation=operation, **value)
        else:
            gtin = get_product_gtin_from_mark(mark)
            product = products.get(gtin)
            if product is None:
                product = _get_product(gtin=gtin)
                products[gtin] = product

            _create_marking_operation(marking_operations, operation, None,
                                      None,
                                      (mark,))

    MarkingOperationMarks.objects.bulk_create(marking_operations)


def clear_raw_marks(operation: MarkingOperation) -> None:
    """Очищает данные сырых марок
    после создание экземпляров MarkingOperationMarks"""
    if RawMark.objects.filter(operation=operation).exists():
        RawMark.objects.filter(operation=operation).delete()


def get_product_gtin_from_mark(mark: str) -> Optional[int]:
    if len(mark) >= 16:
        return int(mark[2:16])
    else:
        return None


def _get_product(gtin: Optional[int] = None,
                 guid: Optional[str] = None) -> Optional[Product]:
    """Поиск номенклатуры по марке либо по GUID"""
    product_filter = {}
    if guid is None:
        product_filter['gtin'] = gtin
    else:
        product_filter['guid'] = guid

    if Product.objects.filter(**product_filter).exists():
        return Product.objects.get(**product_filter)
    else:
        return None


def _create_marking_operation(marking_operation_marks: Iterable,
                              operation: MarkingOperation,
                              product: Optional[Product],
                              aggregation_code: Optional[str],
                              marks: Iterable) -> None:
    """Создает экземпляры модели MarkingOperationMarks
    сырые марки кодируются в base64"""

    for mark in marks:
        mark_bytes = mark.encode("utf-8")
        base64_bytes = base64.b64encode(mark_bytes)
        base64_string = base64_bytes.decode("utf-8")
        marking_operation_marks.append(
            MarkingOperationMarks(operation=operation,
                                  mark=mark,
                                  encoded_mark=base64_string,
                                  product=product,
                                  aggregation_code=aggregation_code))


def _unloaded_marks():
    pass
    # date_filter = datetime.datetime.now() - datetime.timedelta(7)
    # return MarkingOperationMarks.objects.filter(
    #     operation__shift__date__gte=date_filter,
    #     operation__shift__unloaded=False).values('pk', 'operation', 'mark')
