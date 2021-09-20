from django.db import models
import uuid


class BaseModel(models.Model):
    name = models.CharField(verbose_name="Наименование", max_length=1024)
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4,
                            editable=False)

    def __str__(self):
        return self.name


class BaseExternalModel(BaseModel):
    external_key = models.CharField(max_length=36, blank=True)


class Organization(BaseExternalModel):
    pass


class Storage(BaseExternalModel):
    pass


class Department(BaseExternalModel):
    pass


class Device(BaseModel):
    polling_interval = models.PositiveIntegerField()


class Lines(BaseModel):
    storage = models.ForeignKey(Storage, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)


class Property(models.Model):
    name = models.CharField("Наименование", max_length=1024)


class Product(BaseExternalModel):
    gtin = models.CharField(verbose_name="GTIN", max_length=200)
    vendor_code = models.CharField(verbose_name="Артикул", max_length=50)
    properties = models.ManyToManyField(Property, through='ProductProperty')


class ProductProperty(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE,
                                 related_name='product_properties')
    value = models.CharField("Значение", max_length=1024)
