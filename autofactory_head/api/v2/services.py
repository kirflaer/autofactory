from collections.abc import Callable
from typing import NamedTuple, Iterable

from packing.models import MarkingOperationMark, MarkingOperation
from warehouse_management.models import PalletContent


class Field(NamedTuple):
    source: str
    destination: str


def get_marks_to_unload() -> dict:
    data = []
    fields = _get_fields_to_unload()
    values = MarkingOperationMark.objects.filter(operation__ready_to_unload=True, operation__unloaded=False,
                                                 operation__closed=True).values(*[field.source for field in fields])

    aggregation_codes = [element['aggregation_code'] for element in values]
    pallets = {element.code: element.pallet for element in
               PalletContent.objects.filter(aggregation_code__in=aggregation_codes)}

    for value in values:
        element = {field.destination: value[field.source] for field in fields}
        element['production_date'] = value['operation__production_date'].strftime("%d.%m.%Y")
        element['pallet'] = None if pallets.get(value['aggregation_code']) is None else pallets[
            value['aggregation_code']].id
        data.append(element)

    return data


def _get_fields_to_unload() -> Iterable[Field]:
    fields = [Field(source='operation__guid', destination='operation'),
              Field(source='encoded_mark', destination='encoded_mark'),
              Field(source='operation__weight', destination='weight'),
              Field(source='aggregation_code', destination='aggregation_code'),
              Field(source='product__external_key', destination='product'),
              Field(source='operation__production_date', destination='production_date'),
              Field(source='product__is_weight', destination='product_is_weight'),
              Field(source='operation__batch_number', destination='batch_number'),
              Field(source='operation__organization__external_key', destination='organization'),
              Field(source='operation__line__storage__external_key', destination='storage'),
              Field(source='operation__line', destination='line'),
              Field(source='operation__line__department__external_key', destination='department'),
              Field(source='operation__line__type_factory_operation__external_key', destination='type_factory_operation'),
              Field(source='operation__organization__external_key', destination='organization'),
              Field(source='operation__production_date', destination='production_date'),
              Field(source='operation__group', destination='group')]
    return fields
