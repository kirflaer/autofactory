from catalogs.models import (
    Log,
    Device
)

from datetime import datetime as dt
from collections.abc import Iterable
from typing import Optional


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
