from packing.models import MarkingOperationMark
from warehouse_management.models import PalletContent


def get_marks_to_unload() -> list:
    """ Возвращает список марок для выгрузки. Марки по закрытым маркировкам
    С отметкой ready_to_unload
    Функция остается для поддержки старых версий"""

    values = MarkingOperationMark.objects.filter(
        operation__ready_to_unload=True,
        operation__unloaded=False,
        operation__closed=True,
    ).values('encoded_mark',
             'aggregation_code',
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
    aggregation_codes = [element['aggregation_code'] for element in values]
    pallets = {element.code: element.pallet for element in
               PalletContent.objects.filter(aggregation_code__in=aggregation_codes)}

    for value in values:
        element = {'operation': value['operation__guid'],
                   'encoded_mark': value['encoded_mark'],
                   'aggregation_code': value['aggregation_code'],
                   'pallet': None if pallets.get(
                       value['aggregation_code']) is None else pallets[
                       value['aggregation_code']].id,
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
