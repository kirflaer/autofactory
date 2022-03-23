from rest_framework import permissions, status
from rest_framework.response import Response
from .exceptions import ActivationFailed
from catalogs.models import ActivationKey, Device
from datetime import datetime


class IsActivatedDevice(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        token = request.META.get('HTTP_TOKEN')  # временно пока не переведем все девайсы на новую версию
        if token is None:
            return super().has_permission(request, view)

        token = ActivationKey.objects.filter(number=token).first()
        if token is None:
            raise ActivationFailed("Активационный ключ не найден")

        if request.user.device is None:
            raise ActivationFailed("У пользователя не определено устройство")

        if token.TYPE_ACTIVATION == ActivationKey.BY_DATE and token.date > datetime.now():
            raise ActivationFailed("Истек срок действия ключа")

        if token.device.first() is None:
            raise ActivationFailed("У ключа неопределено устройство")

        if token.device.first() != request.user.device:
            raise ActivationFailed("Ключ определен для другого устройста")

        return super().has_permission(request, view)
