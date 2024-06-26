from api.v3.models import MarkingData
from rest_framework.exceptions import APIException
from catalogs.models import Product
from factory_core.models import Shift
from pydantic.error_wrappers import ValidationError
from packing.marking_services import get_base64_string, get_marks_in_shifts
from packing.models import MarkingOperation, MarkingOperationMark


def load_manual_marks(operation: MarkingOperation, data: list) -> None:
    """Загружает данные ручного сканирования"""

    try:
        marking_data = [MarkingData(**element) for element in data]
    except TypeError:
        raise APIException('Переданы некорректные данные, возможно изменен сериализатор маркировки')
    except ValidationError:
        raise APIException('Переданы некорректные данные, возможно изменен сериализатор маркировки')

    products = {}
    marking_marks_instances = []

    marks_in_shift = get_marks_in_shifts(operation.shift)
    valid_marks = set()
    for value in marking_data:
        product = products.get(value.product)
        if product is None:
            product = Product.objects.filter(guid=value.product).first()
            products[value.product] = product

        for mark in value.marks:
            if mark.mark in marks_in_shift:
                continue

            if mark.mark in valid_marks:
                continue

            valid_marks.add(mark.mark)

            values = {
                'operation': operation,
                'mark': mark.mark,
                'encoded_mark': get_base64_string(mark.mark),
                'product': product,
                'aggregation_code': value.aggregation_code,
                'scan_date': mark.scan_date
            }
            marking_marks_instances.append(MarkingOperationMark(**values))

    MarkingOperationMark.objects.bulk_create(marking_marks_instances)


def load_offline_marking_data(instance: MarkingOperation, validated_data: list) -> None:
    shift = Shift.objects.filter(code_offline=instance.group_offline).first()
    if shift is None:
        shift = Shift.objects.create(line=instance.line,
                                     batch_number=instance.batch_number,
                                     production_date=instance.production_date,
                                     code_offline=instance.group_offline,
                                     author=instance.author)
    instance.shift = shift
    instance.group = shift.pk
    instance.is_offline_operation = True
    instance.closed = True
    instance.save()
    load_manual_marks(instance, validated_data)
