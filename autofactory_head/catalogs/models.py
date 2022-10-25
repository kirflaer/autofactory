import uuid

from django.db import models
from django.db.models import UniqueConstraint


class BaseModel(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=1024)
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class BaseExternalModel(BaseModel):
    class Meta:
        abstract = True

    external_key = models.CharField(max_length=36, blank=True, verbose_name='Внешний ключ')


class Organization(BaseExternalModel):
    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Оранизации'


class Client(BaseExternalModel):
    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'


class Direction(BaseExternalModel):
    class Meta:
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'


class Storage(BaseExternalModel):
    store_semi_product = models.BooleanField('Хранит полуфабрикаты', default=False)
    production_without_marking = models.BooleanField('Производство без маркировки', default=False)

    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'


class Department(BaseExternalModel):
    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'


class TypeFactoryOperation(BaseExternalModel):
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Тип производственной операции'
        verbose_name_plural = 'Типы производственных операций'


class Device(BaseModel):
    AUTO_SCANNER = 'AUTO_SCANNER'
    TABLET = 'TABLET'
    DCT = 'DCT'
    VISION_CONTROLLER = 'VISION_CONTROLLER'

    MODE = (
        (AUTO_SCANNER, AUTO_SCANNER),
        (TABLET, TABLET),
        (DCT, DCT),
        (VISION_CONTROLLER, VISION_CONTROLLER)
    )

    mode = models.CharField(max_length=255, choices=MODE, default=DCT)
    is_active = models.BooleanField(default=True, verbose_name='Действует')
    identifier = models.CharField(verbose_name='IP/MAC/ID', blank=True,
                                  null=True,
                                  max_length=50)

    empty_mark_reg_exp = models.ForeignKey('RegularExpression', blank=True,
                                           null=True,
                                           verbose_name='Регулярное выражение пустого пакета',
                                           on_delete=models.CASCADE)

    port = models.PositiveIntegerField(verbose_name='Порт', blank=True,
                                       null=True)
    stream_splitter_code = models.PositiveIntegerField(
        'Разделитель потока сканирования марок', default=0)
    activation_key = models.ForeignKey('ActivationKey', on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='device',
                                       verbose_name='Код активации')

    class Meta:
        verbose_name = 'Устройство'
        verbose_name_plural = 'Устройства'


class Product(BaseExternalModel):
    gtin = models.CharField(default='', blank=True, max_length=50)
    expiration_date = models.PositiveIntegerField('Срок годности', default=0)
    is_weight = models.BooleanField('Весовой товар', default=False)
    semi_product = models.BooleanField('Полуфабрикат', default=False)
    not_marked = models.BooleanField('Немаркируемый', default=False)
    variable_pallet_weight = models.BooleanField('Переменный вес паллеты', default=False)

    class Meta:
        verbose_name = 'Номенклаутра'
        verbose_name_plural = 'Номенклатура'


class Line(BaseModel):
    storage = models.ForeignKey('Storage', on_delete=models.CASCADE, null=True,
                                blank=True, verbose_name='Склад')
    department = models.ForeignKey('Department', on_delete=models.CASCADE,
                                   null=True,
                                   blank=True, verbose_name='Подразделение')
    products = models.ManyToManyField('Product',
                                      through='LineProduct',
                                      verbose_name='Номенклатура')
    type_factory_operation = models.ForeignKey('TypeFactoryOperation',
                                               on_delete=models.CASCADE,
                                               null=True,
                                               blank=True,
                                               verbose_name='Тип пр. операции')

    class Meta:
        verbose_name = 'Линия производства'
        verbose_name_plural = 'Линии производства'


class LineDevice(models.Model):
    line = models.ForeignKey('Line', on_delete=models.CASCADE, null=True,
                             blank=True,
                             verbose_name='Линия')
    device = models.ForeignKey('Device', on_delete=models.CASCADE, null=True,
                               blank=True,
                               verbose_name='Устройство')

    class Meta:
        verbose_name = 'Устройство линии'
        verbose_name_plural = 'Устройства линии'
        constraints = [UniqueConstraint(fields=['line', 'device'],
                                        name='unique_devices')]


class LineProduct(models.Model):
    line = models.ForeignKey('Line', on_delete=models.CASCADE, null=True,
                             blank=True,
                             verbose_name='Линия')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True,
                                blank=True,
                                verbose_name='Номенклатура')

    class Meta:
        verbose_name = 'Номенклатура линии'
        verbose_name_plural = 'Номенклатура линии'
        constraints = [UniqueConstraint(fields=['line', 'product'],
                                        name='unique_products')]


class Unit(BaseExternalModel):
    product = models.ForeignKey('Product', on_delete=models.CASCADE,
                                verbose_name='Номенклатура',
                                related_name='units')
    count_in_pallet = models.PositiveIntegerField('Количество в паллете',
                                                  default=0)

    capacity = models.PositiveIntegerField('Вместимость', default=0)
    is_default = models.BooleanField('Упаковка по умолчанию', default=False)
    gtin = models.CharField(default='', blank=True, max_length=50,
                            verbose_name='Штрихкод')

    class Meta:
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'


class Log(models.Model):
    data = models.TextField(verbose_name='Данные лога')
    device = models.ForeignKey('Device', verbose_name='Устройство', null=True,
                               blank=True, on_delete=models.CASCADE)
    app_version = models.CharField(verbose_name='Версия устройства',
                                   max_length=255)
    server_version = models.CharField(verbose_name='Версия промежуточной',
                                      max_length=255)
    username = models.CharField(verbose_name='Имя пользователя',
                                max_length=255)
    date = models.DateTimeField('Дата создания', auto_now_add=True)
    level = models.CharField('Уровень логирования', max_length=255,
                             default='ERROR')

    class Meta:
        verbose_name = 'Журнал'
        verbose_name_plural = 'Журналы'


class ExternalSource(models.Model):
    name = models.CharField(verbose_name='Наименование', max_length=1024)
    external_key = models.CharField(verbose_name='Внешний ключ', max_length=1024)
    number = models.CharField(verbose_name='Номер', max_length=1024)
    date = models.CharField(verbose_name='Дата', max_length=1024, blank=True,
                            default="")
    creation_date = models.DateTimeField('Дата создания', auto_now_add=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Внешний источник'
        verbose_name_plural = 'Внешние источники'

    def __str__(self):
        return self.name


class RegularExpression(models.Model):
    AGGREGATION_CODE = 'AGGREGATION_CODE'
    MARK = 'MARK'
    EMPTY_DATA_STREAM = 'EMPTY_DATA_STREAM'
    MARK_AUTO_SCANNER = 'MARK_AUTO_SCANNER'

    TYPE_EXPRESSION = (
        (AGGREGATION_CODE, AGGREGATION_CODE),
        (MARK, MARK),
        (EMPTY_DATA_STREAM, EMPTY_DATA_STREAM),
        (MARK_AUTO_SCANNER, MARK_AUTO_SCANNER)
    )

    type_expression = models.CharField(max_length=255, choices=TYPE_EXPRESSION,
                                       default=AGGREGATION_CODE)
    value = models.CharField(verbose_name='Значение', max_length=1024,
                             default='(01){GS1}')

    def __str__(self):
        return self.value


class ActivationKey(models.Model):
    PERPETUAL = 'PERPETUAL'
    BY_DATE = 'BY_DATE'

    TYPE_ACTIVATION = (
        (PERPETUAL, PERPETUAL),
        (BY_DATE, BY_DATE),
    )

    type_activation = models.CharField(max_length=255, choices=TYPE_ACTIVATION,
                                       default=PERPETUAL)
    number = models.CharField(verbose_name='Идентификатор', max_length=1024)
    date = models.DateField('Дата окончания', blank=True, null=True)

    class Meta:
        verbose_name = 'Ключ активации'
        verbose_name_plural = 'Ключи активации'

    def __str__(self):
        return self.number


class StorageCell(BaseExternalModel):
    barcode = models.CharField('Штрихкод', max_length=100, default='-')

    class Meta:
        verbose_name = 'Складская ячейка'
        verbose_name_plural = 'Складские ячейки'
