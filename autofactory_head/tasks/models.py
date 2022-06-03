from django.db import models

from factory_core.models import BaseModel, ExternalSystemExchangeMixin


class TaskType(models.TextChoices):
    # Приемка на склад
    ACCEPTANCE_TO_STOCK = 'ACCEPTANCE_TO_STOCK'
    # Заявки на завод
    PLANT_APPLICATION = 'PLANT_APPLICATION'
    # Заказы
    ORDER = 'ORDER'


class TaskStatus(models.TextChoices):
    NEW = 'NEW'
    WORK = 'WORK'
    CLOSE = 'CLOSE'


class Task(BaseModel, ExternalSystemExchangeMixin):
    type_task = models.CharField(max_length=255, choices=TaskType.choices,
                                 default=TaskType.ACCEPTANCE_TO_STOCK,
                                 verbose_name='Тип задания')

    parent_task = models.ForeignKey('self', on_delete=models.CASCADE,
                                    verbose_name='Родительское задание',
                                    null=True,
                                    blank=True)

    status = models.CharField(max_length=255, choices=TaskStatus.choices, default=TaskStatus.NEW,
                              verbose_name='Статус')

    # products = models.ManyToManyField(Product, through='TaskProduct',
    #                                   verbose_name='Номенклатура задания')
    # pallets = models.ManyToManyField(Pallet, through='TaskPallet',
    #                                  verbose_name='Паллеты задания')
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             verbose_name='Пользователь', null=True,
                             blank=True)
    # client = models.ForeignKey(Client, on_delete=models.CASCADE,
    #                            verbose_name='Клиент', null=True,
    #                            blank=True)
    # direction = models.ForeignKey(Direction, on_delete=models.CASCADE,
    #                               verbose_name='Направление', null=True,
    #                               blank=True)
    external_source = models.ForeignKey(ExternalSource,
                                        on_delete=models.CASCADE,
                                        verbose_name='Внешний источник',
                                        null=True,
                                        blank=True)


    class Meta:
        abstract = True

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
    # product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True,
    #                             blank=True,
    #                             verbose_name='Номенклатура')
    weight = models.FloatField(verbose_name='Вес', default=0.0)
    # count = models.PositiveIntegerField(verbose_name='Количество', default=0.0)
    #
    # class Meta:
    #     constraints = [UniqueConstraint(fields=['task', 'product'],
    #                                     name='unique_task_product')]


# class TaskPallet(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True,
#                              blank=True,
#                              verbose_name='Задание')
#     pallet = models.ForeignKey(Pallet, on_delete=models.CASCADE, null=True,
#                                blank=True,
#                                verbose_name='Паллета')
#
#     class Meta:
#         constraints = [UniqueConstraint(fields=['task', 'pallet'],
#                                         name='unique_task_pallet')]
