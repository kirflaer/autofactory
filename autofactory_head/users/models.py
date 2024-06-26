from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import UniqueConstraint

from catalogs.models import Line, Device, RegularExpression, Storage


class UIElement(models.Model):
    name = models.CharField('Имя', max_length=155)
    identifier = models.CharField('Идентификатор', max_length=155)

    class Meta:
        verbose_name = 'UI элемент'
        verbose_name_plural = 'UI элементы'

    def __str__(self):
        return self.name


class UserMode(models.Model):
    name = models.CharField('Имя', max_length=155)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Режим интерфейса'
        verbose_name_plural = 'Режимы интерфейса'


class UserElement(models.Model):
    mode = models.ForeignKey('UserMode', on_delete=models.CASCADE, null=True,
                             blank=True, verbose_name='Режим')
    element = models.ForeignKey('UIElement', on_delete=models.CASCADE, null=True,
                                blank=True,
                                verbose_name='UI элемент')

    class Meta:
        verbose_name = 'UI элементы пользовательского режма'
        verbose_name_plural = 'UI элементы пользовательского режма'
        constraints = [UniqueConstraint(fields=['mode', 'element'],
                                        name='unique_uni_elements')]


class Setting(models.Model):
    ALL_IN_DAY_BY_LINE = 'ALL_IN_DAY_BY_LINE'
    ALL_IN_DAY_BY_BAT_NUMBER = 'ALL_IN_DAY_BY_BAT_NUMBER'
    ALL_IN_DAY_BY_LINE_BY_BAT_NUMBER = 'ALL_IN_DAY_BY_LINE_BY_BAT_NUMBER'

    TYPE_MARKING_CLOSE = (
        (ALL_IN_DAY_BY_LINE_BY_BAT_NUMBER, ALL_IN_DAY_BY_LINE_BY_BAT_NUMBER),
        (ALL_IN_DAY_BY_BAT_NUMBER, ALL_IN_DAY_BY_BAT_NUMBER),
        (ALL_IN_DAY_BY_LINE, ALL_IN_DAY_BY_LINE)
    )

    type_marking_close = models.CharField(max_length=255,
                                          choices=TYPE_MARKING_CLOSE,
                                          default=ALL_IN_DAY_BY_BAT_NUMBER)

    name = models.CharField(max_length=100, blank=True, default='base settings')
    use_organization = models.BooleanField('Использовать организацию', default=False)
    pallet_passport_template = models.TextField('Шаблон паллетного паспорта', blank=True)
    collect_pallet_mode_is_active = models.BooleanField('Доступен режим сбора паллет', default=False)
    label_template = models.TextField('Шаблон этикетки', blank=True)
    label_sizes = models.CharField('Размеры этикеток', max_length=255, blank=True)
    use_cache = models.BooleanField('Использовать кэш', default=False)
    ttl_cache = models.PositiveIntegerField('Время жизни кэша (сек)', default=600)

    # Секция настроек для дашборда
    show_raw_marking = models.BooleanField('Отображать сырые марки на главном дашборде', default=False)

    # Секция по работе со сменами
    shift_open_show_type_marking = models.BooleanField('Запрашивать тип маркировки при открытии смены', default=True)
    shift_open_show_product = models.BooleanField('Показывать номенклатуру при открытии смены', default=False)
    shift_close_show_pallet_count = models.BooleanField('Показывать собранные паллеты при закрытии смены',
                                                        default=False)
    shift_close_show_marks_count = models.BooleanField('Показывать собранные марки при закрытии смены',
                                                       default=False)

    # Запрос на контроль веса
    use_control_scanning_weight = models.BooleanField(
        'Включить запрос весового ШК, для контроля веса товаров с фиксированным весом', default=False)
    interval_control_scanning_weight = models.PositiveIntegerField('Интервал запроса (в штуках)', default=50)

    class Meta:
        verbose_name = 'Настройки пользователя'
        verbose_name_plural = 'Настройки пользователя'

    def __str__(self):
        return self.name


class User(AbstractUser):
    ERROR = 'ERROR'
    WARNING = 'WARNING'
    INFO = 'INFO'

    LEVEL = (
        (ERROR, ERROR),
        (INFO, INFO),
        (WARNING, WARNING),
    )

    VISION_OPERATOR = 'VISION_OPERATOR'
    VISION_MASTER = 'VISION_MASTER'
    PACKER = 'PACKER'
    PALLET_COLLECTOR = 'PALLET_COLLECTOR'
    REJECTER = 'REJECTER'
    SERVICE = 'SERVICE'
    LOADER = 'LOADER'
    STOREKEEPER = 'STOREKEEPER'
    WAREHOUSE_MASTER = 'WAREHOUSE_MASTER'

    ROLE = (
        (VISION_OPERATOR, VISION_OPERATOR),
        (PACKER, PACKER),
        (PALLET_COLLECTOR, PALLET_COLLECTOR),
        (REJECTER, REJECTER),
        (SERVICE, SERVICE),
        (LOADER, LOADER),
        (STOREKEEPER, STOREKEEPER),
        (WAREHOUSE_MASTER, WAREHOUSE_MASTER)
    )

    role = models.CharField(max_length=255, choices=ROLE, default=PACKER,
                            verbose_name='Роль')
    email = models.EmailField(
        help_text="email address", blank=True, unique=False, default='-')

    bio = models.TextField(blank=True)

    confirmation_code = models.CharField(
        max_length=100, unique=True, blank=True, null=True)

    settings = models.ForeignKey(Setting, on_delete=models.CASCADE,
                                 null=True, blank=True)

    line = models.ForeignKey(Line, blank=True,
                             on_delete=models.CASCADE, null=True,
                             verbose_name='Линия')
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True,
                               blank=True, verbose_name='Устройство',
                               related_name='user_devices')
    scanner = models.ForeignKey(Device, on_delete=models.CASCADE, null=True,
                                blank=True, verbose_name='Сканер',
                                related_name='user_scanners')
    vision_controller = models.ForeignKey(Device, on_delete=models.CASCADE,
                                          null=True,
                                          blank=True,
                                          verbose_name='Контр. тех. зрения',
                                          related_name='vision_controller')
    use_aggregations = models.BooleanField('Использовать агрегацию',
                                           default=False)

    shop = models.ForeignKey(Storage, verbose_name='Цех', blank=True, null=True, on_delete=models.SET_NULL)

    USERNAME_FIELD = "username"

    log_level = models.CharField('Уровень логирования', max_length=255,
                                 choices=LEVEL, default=ERROR)
    inactive_sound_enabled = models.BooleanField(
        'Включать звуковое оповещение при не активности', default=False)
    inactive_period_in_sec = models.PositiveIntegerField('Интервал оповещения',
                                                         default=0)
    is_local_admin = models.BooleanField(
        verbose_name='Локальный администратор', default=False)

    refresh_timeout = models.IntegerField('Интервал обновления', default=10,
                                          validators=[MinValueValidator(4), MaxValueValidator(1200)])
    data_send_interval = models.IntegerField('Интервал отправки данных', default=10,
                                             validators=[MinValueValidator(4), MaxValueValidator(1200)])
    default_page = models.CharField('Страница по умолчанию', default='', max_length=100, blank=True, null=True)
    disable_production_date_filter = models.BooleanField('Отключить фильтр по дате выработки', default=False)

    privileged_user = models.BooleanField('Привилегированный пользователь', default=False)
    mode = models.ForeignKey('UserMode', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Режим')
    show_in_list = models.BooleanField('Показывать в списке', default=False)

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class ConfigEvent(models.Model):
    LOG_REQUEST = 'LOG_REQUEST'
    CUSTOM = 'CUSTOM'
    TABLE_UPDATE = 'TABLE_UPDATE'

    SERVICE_TYPE = (
        (LOG_REQUEST, LOG_REQUEST),
        (CUSTOM, CUSTOM),
        (TABLE_UPDATE, TABLE_UPDATE),
    )

    type_event = models.CharField(max_length=255, choices=SERVICE_TYPE,
                                  default=CUSTOM,
                                  verbose_name='Тип события')

    user = models.ForeignKey(User, verbose_name='Пользователь',
                             on_delete=models.CASCADE)
    argument = models.CharField(verbose_name='Параметр', max_length=255)

    class Meta:
        verbose_name = 'Настройка событий логирования'
        verbose_name_plural = 'Настройка событий логирования'
