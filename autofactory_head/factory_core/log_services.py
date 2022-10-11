from collections.abc import Iterable
from datetime import datetime as dt
from typing import Optional

from catalogs.models import (
    Log,
    Device
)


def log_line_decode(data: str) -> str:
    """Декодирует строку логов из базы.
    Представляя ее в читабельном виде с отступами и переносом строки"""
    log_data = data.encode("utf8").decode("unicode-escape").encode(
        "latin1").decode('utf8')
    return log_data


def logs_summary_data(device: Device, date_source: Optional[str]) -> str:
    """Формирует суммарно все логи по конкретному устройству
    за конкретную дату"""

    table_filter = {}
    if date_source is None or not len(date_source):
        now = dt.now()
        table_filter['year'] = now.year
        table_filter['month'] = now.month
        table_filter['day'] = now.day
    else:
        date_parse = date_source.split('-')
        table_filter['year'] = int(date_parse[0])
        table_filter['month'] = int(date_parse[1])
        table_filter['day'] = int(date_parse[2])

    table_filter['device'] = device
    logs_raw_data = _get_log_data(**table_filter)
    return map(log_line_decode, logs_raw_data)


def _get_log_data(device: Device, year: int, month: int, day: int) -> Iterable:
    """ Получает данные ежедневных отчетов за выбранный период"""
    return Log.objects.filter(
        date__year=year, date__month=month, date__day=day,
        device=device).values_list('data', flat=True)


def get_log_filters(request_data: dict) -> dict:
    """ Формирует словарь для получения фильтров логов"""
    log_filter = {}

    # TODO сделать универсально через class.__dict__
    filters = dict()
    filters['device_id'] = 'device'
    filters['level'] = 'level'
    filters['username'] = 'username'
    filters['app_version'] = 'app_version'
    filters['log_level'] = 'log_level'
    date_raw = request_data.get('date')

    for filter_field_name, request_field_name in filters.items():
        value = request_data.get(request_field_name)
        if value is not None and value != 'none' and len(value):
            log_filter[filter_field_name] = value

    if date_raw is not None and len(date_raw):
        date_parse = date_raw.split('-')
        log_filter['date__year'] = int(date_parse[0])
        log_filter['date__month'] = int(date_parse[1])
        log_filter['date__day'] = int(date_parse[2])

    return log_filter
