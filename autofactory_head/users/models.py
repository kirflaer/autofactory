from django.db import models
from django.contrib.auth.models import AbstractUser
from catalogs.models import Line


class User(AbstractUser):
    email = models.EmailField(
        help_text="email address", blank=False, unique=True)
    bio = models.TextField(blank=True)

    confirmation_code = models.CharField(
        max_length=100, unique=True, blank=True, null=True)

    line = models.ForeignKey(Line, blank=True,
                             on_delete=models.CASCADE, null=True)

    USERNAME_FIELD = "username"

    def __str__(self):
        return self.username
