from django.db import models
from django.contrib.auth.models import AbstractUser
from catalogs.models import Line, Device


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

    name = models.CharField(max_length=100, blank=True,
                            default='base settings')
    use_organization = models.BooleanField('Использовать организацию',
                                           default=False)
    pallet_passport_template = models.TextField('Шаблон паллетного паспорта',
                                                blank=True)
    collect_pallet_mode_is_active = models.BooleanField(
        'Доступен режим сбора паллет', default=False)

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

    ROLE = (
        (VISION_OPERATOR, VISION_OPERATOR),
        (PACKER, PACKER),
        (PALLET_COLLECTOR, PALLET_COLLECTOR),
        (REJECTER, REJECTER),
        (SERVICE, SERVICE),
        (LOADER, LOADER)
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

    USERNAME_FIELD = "username"

    log_level = models.CharField('Уровень логирования', max_length=255,
                                 choices=LEVEL, default=ERROR)
    inactive_sound_enabled = models.BooleanField(
        'Включать звуковое оповещение при неактивности', default=False)
    inactive_period_in_sec = models.PositiveIntegerField('Интервал оповещения',
                                                         default=0)
    is_local_admin = models.BooleanField(
        verbose_name='Локальный администратор', default=False)

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
