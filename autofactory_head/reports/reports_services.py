from datetime import datetime as dt
from datetime import timedelta
from enum import Enum
from typing import Iterable

import pytz
from django.db import connection

from catalogs.models import Line


class ReportType(Enum):
    LINE_LOAD = 1
    LINE_LOAD_BY_HOURS = 2


def get_report_data(user_filters: dict, report_type: ReportType) -> Iterable:
    reports_function = {
        ReportType.LINE_LOAD: _get_load_lines_data,
        ReportType.LINE_LOAD_BY_HOURS: _get_load_lines_data_by_hours
    }

    required_params = {
        ReportType.LINE_LOAD: {'date_start', 'date_end'},
        ReportType.LINE_LOAD_BY_HOURS: {'date_start', 'date_end', 'line'}
    }

    validated_params = dict()
    for key, value in user_filters.items():
        if len(value) and value != 'none':
            validated_params[key] = value

    if not len(validated_params) or not reports_function.get(report_type):
        return []

    if len(set(validated_params.keys()) & required_params[report_type]) != len(required_params[report_type]):
        return []

    if validated_params.get('date_start') is not None:
        validated_params['date_start'] = dt.strptime(validated_params['date_start'], "%Y-%m-%d") - timedelta(hours=3)

    if validated_params.get('date_end') is not None:
        date_end = dt.strptime(validated_params['date_end'], "%Y-%m-%d")
        date_end = date_end.replace(hour=23, minute=59, second=59, microsecond=0, tzinfo=pytz.UTC)
        validated_params['date_end'] = date_end

    return reports_function[report_type](validated_params)


def _get_load_lines_data(params: dict) -> Iterable:
    if params.get('line') is None:
        lines = Line.objects.filter(storage=params['stock']).values_list('pk', flat=True)
    else:
        lines = (params['line'],)

    return _get_load_lines_rows(tuple(map(str, lines)), params.get('date_start'), params.get('date_end'))


def _get_load_lines_data_by_hours(params: dict) -> Iterable:
    return _get_load_lines_hours_rows(params.get('line'), params.get('date_start'), params.get('date_end'))


def _get_load_lines_rows(lines: tuple, date_start: dt, date_end: dt) -> Iterable:
    with connection.cursor() as cursor:
        cursor.execute("""
        Select r.day as day, r.line as line, r.storage as storage, r.line_guid as line_guid,
            COUNT(r.minutes) as activ, 1440 - COUNT(r.minutes) as not_active from
            (SELECT DISTINCT ON (minutes,line) DATE_TRUNC('minute', marks.scan_date AT TIME ZONE 'Europe/Moscow') AS minutes,
            DATE_TRUNC('day', marks.scan_date AT TIME ZONE 'Europe/Moscow') AS day, 
            lines.name as line,
            lines.guid as line_guid,
            storages.name as storage
            FROM
            packing_markingoperationmark as marks
            INNER JOIN packing_markingoperation ON (marks.operation_id = packing_markingoperation.guid)
            LEFT JOIN catalogs_line as lines ON (packing_markingoperation.line_id = lines.guid) 
            LEFT JOIN catalogs_storage as storages ON (lines.storage_id = storages.guid) 	
            WHERE 
            (packing_markingoperation.line_id IN %s AND 
            DATE_TRUNC('day', marks.scan_date AT TIME ZONE 'Europe/Moscow') BETWEEN %s AND %s) ) as r
        GROUP BY r.day, r.line, r.storage, r.line_guid
        ORDER BY r.day, r.line""", (lines, date_start, date_end))
        return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]


def _get_load_lines_hours_rows(line: str, date_start: dt, date_end: dt) -> Iterable:
    with connection.cursor() as cursor:
        cursor.execute("""
        WITH mark_data AS (  
        SELECT 
        DATE_TRUNC('minute', marks.scan_date AT TIME ZONE 'Europe/Moscow') AS minutes,
        DATE_TRUNC('day', marks.scan_date AT TIME ZONE 'Europe/Moscow') AS day,
        DATE_TRUNC('hour', marks.scan_date AT TIME ZONE 'Europe/Moscow') AS hour,
        products.name as product, 
        marks.mark as mark
        FROM
        packing_markingoperationmark as marks
        INNER JOIN packing_markingoperation as operations ON(marks.operation_id = operations.guid)
        INNER JOIN catalogs_product as products ON(marks.product_id = products.guid)
        WHERE (
        operations.line_id = %s AND DATE_TRUNC('day', marks.scan_date AT TIME ZONE 'Europe/Moscow') BETWEEN %s AND %s)
        ) 
        SELECT
        sub_req_1.day, sub_req_1.hour, sub_req_1.product, sub_req_1.count, sub_req_2.activ 
        FROM         
            (
            select SUM(prod_req.count) as count, 
            string_agg(prod_req.product, ', ') as product, 
            prod_req.day, 
            prod_req.hour 
            from (
                 select 
                 COUNT(mark_data.mark) as count, 
                 mark_data.hour, 
                 mark_data.day, 
                 mark_data.product as product
                from mark_data
                GROUP BY mark_data.hour, mark_data.day, mark_data.product 
            ) as prod_req
            GROUP BY prod_req.day, prod_req.hour
        ) as sub_req_1
        
        LEFT JOIN (
            Select activ_req.day, activ_req.hour, COUNT(activ_req.minutes) as activ
            from (
                SELECT DISTINCT ON (minutes) 
                mark_data.hour, mark_data.day, mark_data.minutes
                from mark_data
            ) as activ_req
            GROUP BY activ_req.day, activ_req.hour 
        ) as sub_req_2 ON(sub_req_1.day = sub_req_2.day and sub_req_1.hour = sub_req_2.hour)
        
        ORDER BY sub_req_1.day, sub_req_1.hour
        """, (line, date_start, date_end))
        return [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
