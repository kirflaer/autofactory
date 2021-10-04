from catalogs.models import Product
import datetime
from .models import MarkingOperationMarks, MarkingOperation
import base64


def fill_marks(marking, marks):
    for value in marks:
        if type(marks) == type([]):
            mark = value
        else:
            mark = value['mark']

        sku = mark[2:15]
        product = None
        if Product.objects.filter(sku=sku).exists():
            product = Product.objects.get(sku=sku)

        mark_bytes = mark.encode("utf-8")
        base64_bytes = base64.b64encode(mark_bytes)
        base64_string = base64_bytes.decode("utf-8")
        MarkingOperationMarks.objects.create(operation=marking,
                                             mark=mark,
                                             encoded_mark=base64_string,
                                             product=product)


def unloaded_marks():
    date_filter = datetime.datetime.now() - datetime.timedelta(7)
    return MarkingOperationMarks.objects.filter(
        operation__shift__date__gte=date_filter,
        operation__shift__unloaded=False).values('pk', 'operation', 'mark')
