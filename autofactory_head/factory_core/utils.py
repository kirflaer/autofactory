import datetime
from .models import ShiftOperation


def register_for_exchange():
    start_date = datetime.datetime.now()
    start_date = start_date.replace(hour=0, minute=0, second=0)
    end_date = datetime.datetime.now()
    end_date = end_date.replace(hour=23, minute=59, second=59)
    shifts = ShiftOperation.objects.filter(date__range=[start_date, end_date])
    need_exchange = True
    for shift in shifts:
        if not shift.closed:
            need_exchange = False
            break

    if need_exchange:
        for shift in shifts:
            shift.ready_to_unload = True
            shift.save()
