from rest_framework import status
from rest_framework.exceptions import APIException


class ActivationFailed(APIException):
    status_code = status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS


class BadRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
