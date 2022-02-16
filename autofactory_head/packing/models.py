import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import UniqueConstraint

from catalogs.models import Device, Line, ExternalSource
from factory_core.models import BaseModel
from catalogs.models import Product, Organization, Direction, Client

User = get_user_model()


class MarkingOperation(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               verbose_name='Автор', null=True)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE,
                                     verbose_name='Организация', blank=True,
                                     null=True)

    device = models.ForeignKey(Device, on_delete=models.CASCADE,
                               verbose_name='Устройство', null=True,
                               blank=True, )
    manual_editing = models.BooleanField(default=False)
    batch_number = models.CharField(max_length=150,
                                    verbose_name='Номер партии', blank=True,
                                    null=True)
    production_date = models.DateField('Дата выработки')

    line = models.ForeignKey(Line, on_delete=models.CASCADE,
                             verbose_name='Линия', blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура', blank=True,
                                null=True)


class MarkingOperationMark(models.Model):
    operation = models.ForeignKey(MarkingOperation, on_delete=models.CASCADE,
                                  related_name='marks')
    mark = models.CharField(max_length=500)
    encoded_mark = models.CharField(max_length=500, null=True)
    aggregation_code = models.CharField(max_length=500, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура', blank=True,
                                null=True)


class RawMark(models.Model):
    operation = models.ForeignKey(MarkingOperation, on_delete=models.CASCADE,
                                  related_name='raw_marks')
    mark = models.CharField(max_length=500)


class Pallet(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)
    id = models.CharField(verbose_name='Идентификатор', blank=True,
                          null=True,
                          max_length=50)
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                verbose_name='Номенклатура', blank=True,
                                null=True)
    date = models.DateTimeField('Дата создания', auto_now_add=True)
    is_confirmed = models.BooleanField('Подтверждена', default=False)


class PalletCode(models.Model):
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE,
                               related_name='codes')
    code = models.CharField(max_length=500)


class Task(BaseModel):
    NEW = 'NEW'
    WORK = 'WORK'
    CLOSE = 'CLOSE'

    STATUS = (
        (NEW, NEW),
        (WORK, WORK),
        (CLOSE, CLOSE),
    )

    # Приемка на склад
    ACCEPTANCE_TO_STOCK = 'ACCEPTANCE_TO_STOCK'
    # Заявки на завод
    PLANT_APPLICATION = 'PLANT_APPLICATION'
    # Заказы
    ORDER = 'ORDER'
    TYPE_TASK = (
        (ACCEPTANCE_TO_STOCK, ACCEPTANCE_TO_STOCK),
        (ORDER, ORDER),
        (PLANT_APPLICATION, PLANT_APPLICATION),
    )

    type_task = models.CharField(max_length=255, choices=TYPE_TASK,
                                 default=ACCEPTANCE_TO_STOCK,
                                 verbose_name='Тип задания')

    parent_task = models.ForeignKey('self', on_delete=models.CASCADE,
                                    verbose_name='Родительское задание',
                                    null=True,
                                    blank=True)

    status = models.CharField(max_length=255, choices=STATUS, default=NEW,
                              verbose_name='Статус')
    products = models.ManyToManyField(Product, through='TaskProduct',
                                      verbose_name='Номенклатура задания')
    pallets = models.ManyToManyField(Pallet, through='TaskPallet',
                                     verbose_name='Паллеты задания')
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь', null=True,
                             blank=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE,
                               verbose_name='Клиент', null=True,
                               blank=True)
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE,
                                  verbose_name='Направление', null=True,
                                  blank=True)
    external_source = models.ForeignKey(ExternalSource,
                                        on_delete=models.CASCADE,
                                        verbose_name='Внешний источник',
                                        null=True,
                                        blank=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.type_task == 'ORDER' and not self.date is None:
            child_task_count = Task.objects.filter(
                parent_task=self.parent_task, status='NEW').exclude(
                guid=self.guid).count()
            if child_task_count == 0:
                self.parent_task.status = 'WORK'
                self.parent_task.save()

        super().save(force_insert, force_update, using, update_fields)


class TaskProduct(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True,
                             blank=True,
                             verbose_name='Задание')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True,
                                blank=True,
                                verbose_name='Номенклатура')
    weight = models.FloatField(verbose_name='Вес', default=0.0)
    count = models.PositiveIntegerField(verbose_name='Количество', default=0.0)

    class Meta:
        constraints = [UniqueConstraint(fields=['task', 'product'],
                                        name='unique_task_product')]


class TaskPallet(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True,
                             blank=True,
                             verbose_name='Задание')
    pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, null=True,
                               blank=True,
                               verbose_name='Паллета')

    class Meta:
        constraints = [UniqueConstraint(fields=['task', 'pallet'],
                                        name='unique_task_pallet')]
