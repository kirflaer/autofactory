from catalogs.models import (
    Organization,
    Department,
    Storage,
    Device,
    Product,
    Line
)

from .models import ShiftOperation

from django.forms import ModelForm, BooleanField


class ShiftOperationForm(ModelForm):
    class Meta:
        model = ShiftOperation
        exclude = ['guid',
                   'pk',
                   'unloaded',
                   'closed',
                   'type_of_shift',
                   'ready_to_unload']


class ProductForm(ModelForm):
    class Meta:
        model = Product
        exclude = ['guid']


class LineForm(ModelForm):
    class Meta:
        model = Line
        exclude = ['guid']


class DepartmentForm(ModelForm):
    class Meta:
        model = Department
        exclude = ['guid']


class StorageForm(ModelForm):
    class Meta:
        model = Storage
        exclude = ['guid']


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        exclude = ['guid']


class OrganizationForm(ModelForm):
    class Meta:
        model = Organization
        exclude = ['guid']
