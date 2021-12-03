from django.db import models
import uuid

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

    external_key = models.CharField(max_length=36, blank=True,
                                    verbose_name='Внешний ключ')


class Organization(BaseExternalModel):
    pass


class Storage(BaseExternalModel):
    pass


class Department(BaseExternalModel):
    pass


class TypeFactoryOperation(BaseExternalModel):
    order = models.PositiveIntegerField('Порядок', default=0)


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
    mark_reg_exp = models.CharField(
        verbose_name='Регулярное выражение для получения марки',
        max_length=150, blank=True)

    empty_mark_reg_exp = models.CharField(
        verbose_name='Регулярное выражение пустой марки',
        max_length=150, blank=True)

    port = models.PositiveIntegerField(verbose_name='Порт', blank=True,
                                       null=True)
    stream_splitter_code = models.PositiveIntegerField(
        'Разделитель потока сканирования марок', default=0)


class Product(BaseExternalModel):
    gtin = models.CharField(default='', blank=True, max_length=50)
    expiration_date = models.PositiveIntegerField('Срок годности', default=0)
    is_weight = models.BooleanField(default=False,
                                    verbose_name='Весовой товар')


class Line(BaseModel):
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE, null=True,
                                blank=True, verbose_name='Склад')
    department = models.ForeignKey(Department, on_delete=models.CASCADE,
                                   null=True,
                                   blank=True, verbose_name='Подразделение')
    products = models.ManyToManyField(Product,
                                      through='LineProduct',
                                      verbose_name='Номенклатура')
    type_factory_operation = models.ForeignKey(TypeFactoryOperation,
                                               on_delete=models.CASCADE,
                                               null=True,
                                               blank=True,
                                               verbose_name='Тип пр. операции')


class LineDevice(models.Model):
    line = models.ForeignKey(Line, on_delete=models.CASCADE, null=True,
                             blank=True,
                             verbose_name='Линия')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True,
                               blank=True,
                               verbose_name='Устройство')

    class Meta:
        constraints = [UniqueConstraint(fields=['line', 'device'],
                                        name='unique_devices')]


class LineProduct(models.Model):
    line = models.ForeignKey(Line, on_delete=models.CASCADE, null=True,
                             blank=True,
                             verbose_name='Линия')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True,
                                blank=True,
                                verbose_name='Номенклатура')

    class Meta:
        constraints = [UniqueConstraint(fields=['line', 'product'],
                                        name='unique_products')]


class Unit(BaseExternalModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура',
                                related_name='units')
    count_in_pallet = models.PositiveIntegerField('Количество в паллете',
                                                  default=0)

    capacity = models.PositiveIntegerField('Вместимость', default=0)
    is_default = models.BooleanField('Упаковка по умолчанию', default=False)


class Log(models.Model):
    data = models.TextField(verbose_name='Данные лога')
    device = models.ForeignKey(Device, verbose_name='Устройство', null=True,
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
