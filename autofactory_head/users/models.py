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

    def __str__(self):
        return self.name


class User(AbstractUser):
    VISION_OPERATOR = 'VISION_OPERATOR'
    VISION_MASTER = 'VISION_MASTER'
    PACKER = 'PACKER'
    PALLET_COLLECTOR = 'PALLET_COLLECTOR'
    REJECTER = 'REJECTER'

    ROLE = (
        (VISION_OPERATOR, VISION_OPERATOR),
        (PACKER, PACKER),
        (PALLET_COLLECTOR, PALLET_COLLECTOR),
        (REJECTER, REJECTER),
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

    def __str__(self):
        return self.username
