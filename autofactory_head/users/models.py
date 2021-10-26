from django.db import models
from django.contrib.auth.models import AbstractUser
from catalogs.models import Line, Device

from enum import Enum


class Color(Enum):
    BLUE = 3


class User(AbstractUser):
    VISION_OPERATOR = 'VISION_OPERATOR'
    VISION_MASTER = 'VISION_MASTER'
    PACKER = 'PACKER'
    PALLET_COLLECTOR = 'PALLET_COLLECTOR'

    ROLE = (
        (VISION_OPERATOR, VISION_OPERATOR),
        (PACKER, PACKER),
        (PALLET_COLLECTOR, PALLET_COLLECTOR),
    )

    role = models.CharField(max_length=255, choices=ROLE, default=PACKER)
    email = models.EmailField(
        help_text="email address", blank=False, unique=True)
    bio = models.TextField(blank=True)

    confirmation_code = models.CharField(
        max_length=100, unique=True, blank=True, null=True)

    line = models.ForeignKey(Line, blank=True,
                             on_delete=models.CASCADE, null=True)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, null=True,
                               blank=True, verbose_name='Устройство',
                               related_name='user_devices')
    scanner = models.ForeignKey(Device, on_delete=models.CASCADE, null=True,
                                blank=True, verbose_name='Сканер',
                                related_name='user_scanners')
    vision_controller_address = models.CharField(
        verbose_name='Контроллер тех. зрения (адрес)', max_length=150,
        blank=True)

    vision_controller_port = models.PositiveIntegerField(
        verbose_name='Контроллер тех. зрения (порт)', blank=True, null=True)

    USERNAME_FIELD = "username"

    def __str__(self):
        return self.username
