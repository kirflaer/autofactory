from datetime import datetime as dt

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import APIException

from api.serializers import StorageSerializer
from catalogs.models import ExternalSource
from catalogs.serializers import ExternalSerializer
from warehouse_management.models import (AcceptanceOperation, OperationProduct, PalletCollectOperation, OperationPallet,
                                         Pallet, PlacementToCellsOperation,
                                         MovementBetweenCellsOperation, ShipmentOperation, OrderOperation,
                                         PalletProduct, PalletStatus, PalletSource, OperationCell, InventoryOperation,
                                         SelectionOperation, StorageCell,
                                         RepackingOperation, StorageArea,
                                         InventoryAddressWarehouseOperation)
from warehouse_management.warehouse_services import (
    check_and_collect_orders, enrich_pallet_info, get_cell_state
)


class OperationBaseSerializer(serializers.Serializer):
    external_source = ExternalSerializer()


class OrderOperationReadSerializer(serializers.Serializer):
    client_presentation = serializers.CharField()
    number = serializers.CharField()
    date = serializers.DateTimeField(format="%Y-%m-%d")
    guid = serializers.UUIDField()


class OrderOperationWriteSerializer(serializers.ModelSerializer):
    client_presentation = serializers.CharField()

    class Meta:
        fields = ('name', 'external_key', 'number', 'date', 'client_presentation')
        model = ExternalSource


class SuitablePalletSerializer(serializers.Serializer):
    id = serializers.CharField(write_only=True)
    count = serializers.IntegerField()
    priority = serializers.IntegerField()
    guid = serializers.SerializerMethodField(read_only=True, required=False)

    @staticmethod
    def get_guid(obj):
        return obj.pallet.guid


class PalletProductSerializer(serializers.Serializer):
    product = serializers.UUIDField(write_only=True)
    guid = serializers.SlugRelatedField(read_only=True, source='product', slug_field='pk')
    weight = serializers.IntegerField()
    count = serializers.IntegerField()
    batch_number = serializers.IntegerField(required=False)
    production_date = serializers.DateField(required=False)
    external_key = serializers.CharField(required=False)
    order = OrderOperationReadSerializer(required=False)
    order_external_source = OrderOperationWriteSerializer(required=False)
    is_weight = serializers.SerializerMethodField(read_only=True, required=False)
    has_shipped_products = serializers.BooleanField(required=False)
    is_collected = serializers.BooleanField(required=False)
    has_divergence = serializers.BooleanField(required=False)
    series = serializers.CharField(required=False)
    suitable_pallets = SuitablePalletSerializer(many=True, write_only=True)

    @staticmethod
    def get_is_weight(obj):
        if obj.product is None:
            return False

        return obj.product.is_weight


class PalletSourceCreateSerializer(serializers.Serializer):
    pallet_guid = serializers.CharField(source='pallet_source')
    product = serializers.CharField()
    batch_number = serializers.CharField()
    weight = serializers.IntegerField(required=False)
    count = serializers.IntegerField()
    production_date = serializers.DateField()
    external_key = serializers.CharField(required=False)
    additional_collect = serializers.BooleanField(required=False)

    def validate(self, attrs):
        pallet_source = Pallet.objects.filter(guid=attrs.get('pallet_source')).first()
        if not pallet_source:
            raise APIException("Не найдена паллета указанная в качестве источника")

        return super().validate(attrs)


class PalletSourceReadSerializer(serializers.ModelSerializer):
    pallet_id = serializers.SlugRelatedField(slug_field='id', source='pallet_source', read_only=True)
    pallet_guid = serializers.SlugRelatedField(slug_field='guid', source='pallet_source', read_only=True)
    is_weight = serializers.SerializerMethodField(read_only=True, required=False)
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        fields = (
            'product', 'batch_number', 'weight', 'count', 'pallet_id', 'pallet_guid', 'production_date', 'external_key',
            'is_weight', 'user', 'additional_collect')
        model = PalletSource

    @staticmethod
    def get_is_weight(obj):
        return obj.product.is_weight


class PalletWriteSerializer(serializers.Serializer):
    codes = serializers.ListField(required=False)
    id = serializers.CharField(required=False)
    product = serializers.CharField(required=False)
    batch_number = serializers.CharField(required=False)
    production_date = serializers.DateField(required=False)
    content_count = serializers.IntegerField(required=False)
    weight = serializers.IntegerField(required=False)
    external_key = serializers.CharField(required=False)
    products = PalletProductSerializer(many=True, required=False)
    status = serializers.CharField(required=False)
    production_shop = serializers.CharField(required=False)
    pallet_type = serializers.CharField(required=False)
    marking_group = serializers.CharField(required=False)
    shift = serializers.CharField(required=False)
    code_offline = serializers.CharField(required=False)
    cell = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    consignee = serializers.CharField(required=False)


class PalletReadSerializer(serializers.Serializer):
    id = serializers.CharField()
    product_name = serializers.SlugRelatedField(many=False, read_only=True, slug_field='name', source='product')
    product_guid = serializers.SlugRelatedField(many=False, read_only=True, slug_field='pk', source='product')
    status = serializers.CharField()
    creation_date = serializers.DateTimeField(format="%d.%m.%Y")
    batch_number = serializers.CharField()
    weight = serializers.IntegerField()
    count = serializers.IntegerField(source='content_count')
    production_date = serializers.DateField(format="%d.%m.%Y")
    guid = serializers.UUIDField()
    sources = serializers.SerializerMethodField()
    production_shop = serializers.SlugRelatedField(read_only=True, slug_field='pk')
    external_key = serializers.CharField(read_only=True)
    marking_group = serializers.CharField(required=False)
    cell = serializers.SerializerMethodField()
    name = serializers.CharField(required=False)
    consignee = serializers.CharField(required=False)

    @staticmethod
    def get_sources(obj):
        sources = PalletSource.objects.filter(pallet=obj)
        serializer = PalletSourceReadSerializer(sources, many=True)
        return serializer.data

    @staticmethod
    def get_cell(obj):
        change_state_row = get_cell_state(pallet=obj)
        if change_state_row is None:
            return None

        serializer = StorageCellsSerializer(change_state_row.cell)
        return serializer.data


class PalletUpdateSerializer(serializers.ModelSerializer):
    content_count = serializers.IntegerField(required=False)
    id = serializers.CharField(required=False)
    sources = PalletSourceCreateSerializer(many=True, required=False)
    weight = serializers.IntegerField(required=False)
    collected_strings = serializers.ListField(required=False)
    changed_product_keys = []

    class Meta:
        fields = ('status', 'content_count', 'id', 'sources', 'weight', 'collected_strings', 'not_fully_collected')
        model = Pallet

    def update(self, instance, validated_data):
        with transaction.atomic():
            enrich_pallet_info(validated_data, self.changed_product_keys, instance)
        return super().update(instance, validated_data)


class PalletUpdateShipmentSerializer(PalletUpdateSerializer):
    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            check_and_collect_orders(self.changed_product_keys)
        return instance


class PalletUpdateRepackingSerializer(PalletUpdateSerializer):
    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            total_count = 0
            total_weight = 0
            for pallet_row in instance.sources.all():
                if instance.not_fully_collected:
                    pallet_row.pallet_source.status = PalletStatus.ARCHIVED
                    pallet_row.pallet_source.save()
                if not pallet_row.user:
                    pallet_row.user = self.request_user
                    pallet_row.save()

                total_count += pallet_row.count
                total_weight += pallet_row.weight
            instance.content_count = total_count
            instance.weight = total_weight
            instance.save()
            return instance


class OperationProductsSerializer(serializers.Serializer):
    product = serializers.CharField()
    weight = serializers.FloatField(required=False)
    count = serializers.FloatField(required=False)


class OperationCellsSerializer(serializers.Serializer):
    pallet = serializers.CharField()
    cell = serializers.CharField()
    count = serializers.FloatField(required=False)
    cell_destination = serializers.CharField(required=False)
    series = serializers.CharField(required=False)


class PalletCollectOperationWriteSerializer(serializers.Serializer):
    pallets = PalletWriteSerializer(many=True)


class PalletShortSerializer(serializers.ModelSerializer):
    product = serializers.SlugRelatedField(many=False, read_only=True, slug_field='external_key')
    production_shop = serializers.SlugRelatedField(many=False, read_only=True, slug_field='external_key')
    department = serializers.SerializerMethodField()

    class Meta:
        model = Pallet
        fields = (
            'id', 'guid', 'product', 'content_count', 'batch_number', 'production_date', 'status', 'marking_group',
            'weight', 'production_shop', 'department')

    @staticmethod
    def get_department(obj: Pallet):
        if obj.shift and obj.shift.line and obj.shift.line.department:
            return obj.shift.line.department.external_key
        return None


class PalletCollectOperationReadSerializer(serializers.ModelSerializer):
    pallets_semi = serializers.SerializerMethodField()
    pallets_complete = serializers.SerializerMethodField()
    pallets_not_marked = serializers.SerializerMethodField()

    class Meta:
        model = PalletCollectOperation
        fields = ('guid', 'pallets_semi', 'pallets_complete', 'pallets_not_marked')

    @staticmethod
    def get_pallets_not_marked(obj):
        return PalletCollectOperationReadSerializer.get_pallets_data({'operation': obj.guid,
                                                                      'pallet__product__not_marked': True})

    @staticmethod
    def get_pallets_complete(obj):
        return PalletCollectOperationReadSerializer.get_pallets_data({'operation': obj.guid,
                                                                      'pallet__product__semi_product': False,
                                                                      'pallet__product__not_marked': False})

    @staticmethod
    def get_pallets_semi(obj):
        return PalletCollectOperationReadSerializer.get_pallets_data({'operation': obj.guid,
                                                                      'pallet__product__semi_product': True})

    @staticmethod
    def get_pallets_data(product_filter):
        pallets_ids = OperationPallet.objects.filter(**product_filter).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallets_ids).exclude(status=PalletStatus.ARCHIVED)
        serializer = PalletShortSerializer(pallets, many=True)
        return serializer.data


class AcceptanceOperationWriteSerializer(OperationBaseSerializer):
    products = OperationProductsSerializer(many=True)
    pallets = serializers.ListField()
    storage = serializers.CharField()
    production_date = serializers.CharField(required=False)
    batch_number = serializers.CharField(required=False)

    class Meta:
        fields = ('external_source', 'products', 'pallets', 'storage', 'production_date', 'batch_number')


class AcceptanceOperationReadSerializer(serializers.ModelSerializer):
    """ Приемка на склад. Сериализатор для читающих запросов """
    products = serializers.SerializerMethodField()
    storage = StorageSerializer()
    production_date = serializers.DateField(format="%d.%m.%Y")
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    pallets = serializers.SerializerMethodField()
    pallets_count = serializers.SerializerMethodField()
    external_source = ExternalSerializer()
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = AcceptanceOperation
        fields = ('guid', 'number', 'status', 'date', 'storage', 'production_date', 'products', 'pallets',
                  'pallets_count', 'batch_number', 'external_source', 'user')

    @staticmethod
    def get_pallets_count(obj):
        return OperationPallet.objects.filter(operation=obj.guid).count()

    @staticmethod
    def get_pallets(obj):
        pallets_ids = OperationPallet.objects.filter(operation=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallets_ids).exclude(status=PalletStatus.ARCHIVED)
        serializer = PalletReadSerializer(pallets, many=True)
        return serializer.data

    @staticmethod
    def get_products(obj):
        products = OperationProduct.objects.filter(operation=obj.guid)
        result = []
        for element in products:
            result.append(
                {'name': element.product.name,
                 'weight': element.weight,
                 'guid': element.product.guid,
                 'gtin': element.product.gtin,
                 'count': element.count,
                 })
        return result


class StorageCellsSerializer(serializers.ModelSerializer):
    storage_area = serializers.CharField(required=False)

    class Meta:
        fields = ('guid', 'name', 'external_key', 'barcode', 'storage_area', 'needed_scan')
        model = StorageCell
        read_only_fields = ('guid',)

    def create(self, validated_data):
        storage_area_key = validated_data.pop('storage_area')
        storage_area = StorageArea.objects.filter(external_key=storage_area_key).first()
        validated_data['storage_area'] = storage_area
        cell = StorageCell.objects.create(**validated_data)
        return cell


class OperationCellFullSerializer(serializers.ModelSerializer):
    pallet = PalletReadSerializer()
    cell_source = StorageCellsSerializer()
    cell_destination = StorageCellsSerializer(required=False)

    class Meta:
        model = OperationCell
        fields = ('cell_source', 'cell_destination', 'pallet')


class PlacementToCellsOperationWriteSerializer(OperationBaseSerializer):
    cells = OperationCellsSerializer(many=True)
    storage = serializers.CharField(required=False)


class PlacementToCellsOperationReadSerializer(serializers.ModelSerializer):
    storage = StorageSerializer()
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    cells = serializers.SerializerMethodField()
    external_source = ExternalSerializer()

    class Meta:
        model = PlacementToCellsOperation
        fields = ('external_source', 'guid', 'number', 'status', 'date', 'storage', 'cells')

    @staticmethod
    def get_cells(obj):
        cells = OperationCell.objects.filter(operation=obj.guid)
        serializer = OperationCellFullSerializer(cells, many=True)
        return serializer.data


class MovementBetweenCellsOperationWriteSerializer(serializers.Serializer):
    pallet = serializers.CharField()
    cell_source = serializers.CharField()
    cell_destination = serializers.CharField()

    def validate(self, attrs):
        cell_source = StorageCell.objects.filter(guid=attrs.get('cell_source')).first()
        if not cell_source:
            raise APIException('Ячейка источник не найдена.')

        cell_destination = StorageCell.objects.filter(guid=attrs.get('cell_destination')).first()
        if not cell_destination:
            raise APIException('Ячейка назначения не найдена.')

        pallet = Pallet.objects.filter(id=attrs.get('pallet')).first()
        if not pallet:
            raise APIException('Паллета не найдена.')

        return attrs


class MovementBetweenCellsOperationReadSerializer(serializers.ModelSerializer):
    cells = serializers.SerializerMethodField()
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")

    class Meta:
        model = MovementBetweenCellsOperation
        fields = ('guid', 'number', 'status', 'date', 'cells')

    @staticmethod
    def get_cells(obj: MovementBetweenCellsOperation):
        operation: OperationCell = OperationCell.objects.filter(operation=obj.guid).first()
        if not operation:
            return None
        return {
            'cell_source': operation.cell_source.external_key,
            'cell_destination': operation.cell_destination.external_key,
            'pallet': operation.pallet.id
        }


class ShipmentOperationWriteSerializer(serializers.ModelSerializer):
    external_source = ExternalSerializer()
    pallets = PalletWriteSerializer(many=True)
    has_selection = serializers.BooleanField(required=False)
    cells = OperationCellsSerializer(many=True)
    car_carrier = serializers.CharField(required=False)

    class Meta:
        model = ShipmentOperation
        fields = ('direction', 'external_source', 'pallets', 'has_selection', 'manager', 'cells', 'car_carrier')


class OrderReadSerializer(serializers.ModelSerializer):
    pallets = serializers.SerializerMethodField()
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')

    class Meta:
        model = OrderOperation
        fields = ('guid', 'date', 'number', 'status', 'external_key', 'pallets')

    @staticmethod
    def get_pallets(obj):
        pallet_guids = PalletProduct.objects.filter(order=obj.guid).values_list('pallet', flat=True)
        pallets = Pallet.objects.filter(guid__in=pallet_guids)
        result = []
        for pallet in pallets:
            products = PalletProduct.objects.filter(pallet=pallet, order=obj.guid)
            keys = list(products.values_list('external_key', flat=True))
            sources = PalletSource.objects.filter(pallet=pallet, external_key__in=keys)
            result.append({
                'products': PalletProductSerializer(products, many=True).data,
                'sources': PalletSourceReadSerializer(sources, many=True).data
            })
        return result


class ArrivalAtStockOperationWriteSerializer(OperationBaseSerializer):
    products = OperationProductsSerializer(many=True)
    storage = serializers.CharField()

    class Meta:
        fields = ('external_source', 'products', 'storage')


class ArrivalAtStockOperationReadSerializer(serializers.ModelSerializer):
    """ Приход на склад. Сериализатор для читающих запросов """
    products = serializers.SerializerMethodField()
    storage = StorageSerializer()
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    external_source = ExternalSerializer()

    class Meta:
        model = AcceptanceOperation
        fields = ('guid', 'number', 'status', 'date', 'storage', 'products', 'external_source')

    @staticmethod
    def get_products(obj):
        products = OperationProduct.objects.filter(operation=obj.guid)
        serializer = OperationProductsSerializer(products, many=True)
        return serializer.data


class InventoryOperationWriteSerializer(OperationBaseSerializer):
    products = OperationProductsSerializer(many=True)

    class Meta:
        fields = ('external_source', 'products', 'storage')


class OperationInventoryProductsSerializer(serializers.Serializer):
    product = serializers.CharField()
    product_guid = serializers.SlugRelatedField(slug_field='pk', source='product', read_only=True)
    plan = serializers.FloatField(required=False, source='count')
    fact = serializers.FloatField(required=False, source='count_fact')


class InventoryOperationReadSerializer(serializers.ModelSerializer):
    """ Инвентаризация. Сериализатор для читающих запросов """
    products = serializers.SerializerMethodField()
    date = serializers.DateTimeField(format="%d.%m.%Y %H:%M:%S")
    external_source = ExternalSerializer()

    class Meta:
        model = InventoryOperation
        fields = ('guid', 'number', 'status', 'date', 'products', 'external_source')

    @staticmethod
    def get_products(obj):
        products = OperationProduct.objects.filter(operation=obj.guid)
        serializer = OperationInventoryProductsSerializer(products, many=True)
        return serializer.data


class SelectionOperationReadSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    number = serializers.SerializerMethodField()
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')
    storage_areas = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(slug_field='username', read_only=True)

    class Meta:
        model = SelectionOperation
        fields = ('status', 'date', 'number', 'guid', 'external_key', 'user', 'storage_areas')

    @staticmethod
    def get_number(obj):
        return obj.external_source.number.lstrip('0')

    @staticmethod
    def get_date(obj):
        try:
            date = dt.strptime(obj.external_source.date, '%Y-%m-%dT%H:%M:%S')
            date = date.strftime('%d.%m.%Y')
        except ValueError:
            date = obj.date.strftime('%d.%m.%Y')
        return date

    @staticmethod
    def get_storage_areas(obj):
        operation_cells = OperationCell.objects.filter(operation=obj.guid).order_by('cell_source__rack_number',
                                                                                    'cell_source__position')
        storage_areas = {key: [] for key in
                         list(
                             operation_cells.values_list('cell_destination__storage_area__name', flat=True).distinct())}

        for row in operation_cells:
            area = storage_areas.get(row.cell_destination.storage_area.name)
            cell_source = StorageCellsSerializer(row.cell_source)
            cell_destination = StorageCellsSerializer(row.cell_destination)
            pallet = PalletReadSerializer(row.pallet)
            pallet_in_area = {'cell_source': cell_source.data,
                              'cell_destination': cell_destination.data,
                              'pallet': pallet.data}
            area.append(pallet_in_area)

        return [{'name': key, 'pallets': value} for key, value in storage_areas.items()]


class SelectionOperationWriteSerializer(serializers.ModelSerializer):
    external_source = ExternalSerializer()
    cells = OperationCellsSerializer(many=True)

    class Meta:
        model = SelectionOperation
        fields = ('external_source', 'cells')

    def validate(self, attrs):
        for cell in attrs['cells']:
            pallet = Pallet.objects.filter(id=cell['pallet']).first()
            if not pallet:
                raise APIException(f'Не найдена паллета {cell["pallet"]}')
        return super().validate(attrs)


class ChangeCellSerializer(serializers.Serializer):
    cell_source = serializers.CharField()
    cell_destination = serializers.CharField()

    def validate(self, attrs):
        if not StorageCell.objects.filter(guid=attrs.get('cell_source')).first():
            raise APIException('Не найдена ячейка источник')

        if not StorageCell.objects.filter(guid=attrs.get('cell_destination')).first():
            raise APIException('Не найдена ячейка назначения')

        return super().validate(attrs)


class RepackingPalletWriteSerializer(serializers.Serializer):
    pallet = serializers.CharField()
    count = serializers.IntegerField()


class RepackingOperationWriteSerializer(OperationBaseSerializer):
    pallets = RepackingPalletWriteSerializer(many=True)

    class Meta:
        fields = ('external_source', 'pallets')


class RepackingPalletReadSerializer(serializers.ModelSerializer):
    count = serializers.IntegerField(source='content_count')
    sources = serializers.SerializerMethodField()

    class Meta:
        model = Pallet
        fields = ('count', 'guid', 'id', 'sources')

    @staticmethod
    def get_sources(obj):
        sources = PalletSource.objects.filter(pallet=obj)
        serializer = PalletSourceReadSerializer(sources, many=True)
        return serializer.data


class RepackingOperationReadSerializer(serializers.ModelSerializer):
    pallets = serializers.SerializerMethodField()
    external_key = serializers.SlugRelatedField(slug_field='external_key', read_only=True, source='external_source')
    number = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    class Meta:
        model = RepackingOperation
        fields = ('status', 'date', 'number', 'guid', 'pallets', 'external_key')

    @staticmethod
    def get_number(obj):
        return obj.external_source.number.lstrip('0')

    @staticmethod
    def get_date(obj):
        try:
            date = dt.strptime(obj.external_source.date, '%Y-%m-%dT%H:%M:%S')
            date = date.strftime('%d.%m.%Y')
        except ValueError:
            date = obj.date.strftime('%d.%m.%Y')
        return date

    @staticmethod
    def get_pallets(obj):
        pallets = OperationPallet.objects.filter(operation=obj.guid)
        result = []
        for pallet_data in pallets:
            serializer_pallet = PalletReadSerializer(pallet_data.pallet)
            serializer_pallet_depends = PalletReadSerializer(pallet_data.dependent_pallet)
            result.append({'pallet_source': serializer_pallet_depends.data,
                           'pallet_destination': serializer_pallet.data,
                           'count': pallet_data.count})

        return result


class InventoryWithPlacementOperationWriteSerializer(serializers.Serializer):
    pallet = serializers.CharField()
    cell = serializers.CharField()
    count = serializers.IntegerField()
    weight = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if not Pallet.objects.filter(guid=attrs.get('pallet')).first():
            raise APIException('Не найдена паллета')

        if not StorageCell.objects.filter(external_key=attrs.get('cell')).first():
            raise APIException('Не найдена ячейка')

        return super().validate(attrs)


class InventoryWithPlacementOperationReadSerializer(serializers.ModelSerializer):
    pallet = serializers.SerializerMethodField()
    cell = serializers.SerializerMethodField()

    class Meta:
        model = InventoryOperation
        fields = ('pallet', 'cell', 'guid')

    @staticmethod
    def get_pallet(obj):
        row = OperationCell.objects.filter(operation=obj.guid).first()
        if not row:
            return None
        serializer = PalletShortSerializer(row.pallet)
        return serializer.data

    @staticmethod
    def get_cell(obj):
        row = OperationCell.objects.filter(operation=obj.guid).first()
        if not row:
            return None
        return row.cell_source.external_key


class OperationPalletSerializer(serializers.Serializer):
    pallet = serializers.CharField()
    count = serializers.IntegerField()

    def validate(self, attrs):
        pallet = Pallet.objects.filter(id=attrs.get('pallet')).first()
        if not pallet:
            raise APIException(f'Не найдена паллета {attrs.get("pallet")}')

        if pallet.status == PalletStatus.ARCHIVED:
            raise APIException(f'Паллета {attrs.get("pallet")} является архивной')

        return super().validate(attrs)


class InventoryAddressWarehouseSerializer(serializers.ModelSerializer):
    product = serializers.CharField()
    pallet = PalletReadSerializer()
    cell = StorageCellsSerializer()
    plan = serializers.IntegerField()
    fact = serializers.IntegerField()

    class Meta:
        model = InventoryAddressWarehouseOperation
        fields = ('guid', 'product', 'pallet', 'cell', 'plan', 'fact')


class InventoryWriteSerializer(serializers.ModelSerializer):
    product = serializers.CharField()
    pallet = serializers.CharField()
    cell = serializers.CharField()
    plan = serializers.IntegerField()
    fact = serializers.IntegerField(required=False)

    class Meta:
        model = InventoryAddressWarehouseOperation
        fields = ('guid', 'product', 'pallet', 'cell', 'plan', 'fact')
