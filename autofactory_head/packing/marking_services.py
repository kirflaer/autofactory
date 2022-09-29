import base64
import datetime
from collections.abc import Iterable
from datetime import datetime as dt, timedelta
from typing import Optional, Dict, List

import pytz
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q

from catalogs.models import (
    Product
)
from warehouse_management.models import Pallet, OperationPallet, PalletCollectOperation

from .models import (
    RawMark,
    MarkingOperation,
    MarkingOperationMark
)

User = get_user_model()


def get_dashboard_data() -> Dict:
    result = {}
    for key, value in _get_report_week_marking().items():
        result[key] = value
    return result


def _get_report_week_marking() -> Dict:
    labels = []
    data = []
    today = dt.today()
    monday = today - timedelta(dt.weekday(today))
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=pytz.UTC)
    sunday = (today + timedelta(6 - dt.weekday(today))).replace(tzinfo=pytz.UTC)

    report_data = MarkingOperationMark.objects.filter(
        operation__date__range=[monday, sunday]).values(
        'operation__line__name').annotate(count=Count('operation'))
    for element in report_data:
        labels.append(element['operation__line__name'])
        data.append(element['count'])
    return {'week_marking_labels': labels,
            'week_marking_data': data,
            'week_marking_table_data': report_data}


def _get_report_marking_dynamics() -> Dict:
    """ Функция возвращает данные для формирования отчета "Динамика загрузки линий" """
    today = dt.today()
    start_current_month = today - timedelta(days=30)
    start_prev_month = today - timedelta(days=60)

    lines_query_set = MarkingOperation.objects.prefetch_related('line').filter(
        date__range=[start_prev_month, today]).values('line', 'line__name')

    lines = []
    label_lines = []
    for line in lines_query_set:
        if lines.count(line['line']):
            continue
        lines.append(line['line'])
        label_lines.append(line['line__name'])

    result = {'marking_dynamics_labels': label_lines,
              'data_current_month': _get_data_report_marking_dynamics(start_current_month, today, lines),
              'data_prev_month': _get_data_report_marking_dynamics(start_prev_month, start_current_month, lines)
              }

    return result


def _get_data_report_marking_dynamics(start: datetime, end: datetime, lines: List) -> Iterable:
    result = []
    query_set = MarkingOperationMark.objects.prefetch_related('operation').filter(operation__date__range=[start, end])
    for line in lines:
        line_data = query_set.filter(operation__line=line).values('operation__line').annotate(
            count=Count('operation'))
        result.append(0 if not len(line_data) else line_data[0]['count'])
    return result


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

    start_date = datetime.datetime.now() - timedelta(days=1)
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

    need_exchange = not bool(markings.exclude(guid=operation.guid).filter(closed=False).exists())

    if need_exchange:
        markings.update({'ready_to_unload': True})

        groups = list(map(str, [i for i in markings.values_list('group', flat=True) if i is not None]))
        groups += [i for i in markings.values_list('group_offline', flat=True) if i is not None]
        task_pallets = Pallet.objects.filter(marking_group__in=groups)
        tasks_ids = OperationPallet.objects.filter(pallet__in=task_pallets)
        tasks = PalletCollectOperation.objects.filter(guid__in=tasks_ids.values_list('operation', flat=True))

        for marking in markings:
            group = str(marking.group) if marking.group is not None else marking.group_offline
            if group is None:
                continue

            pallets = task_pallets.filter(marking_group=group)


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
            product = operation.product

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


def get_marking_filters(request_data: dict) -> dict:
    """ Формирует словарь для получения """
    marking_filter = {}

    filters = dict()
    filters['author_id'] = 'user'
    filters['line_id'] = 'line'
    filters['batch_number'] = 'batch_number'

    date_source = request_data.get('date_source')

    for filter_field_name, request_field_name in filters.items():
        value = request_data.get(request_field_name)
        if value is not None and value != 'none' and len(value):
            marking_filter[filter_field_name] = value

    if date_source is not None and len(date_source):
        date_parse = date_source.split('-')
        marking_filter['date__year'] = int(date_parse[0])
        marking_filter['date__month'] = int(date_parse[1])
        marking_filter['date__day'] = int(date_parse[2])

    return marking_filter
