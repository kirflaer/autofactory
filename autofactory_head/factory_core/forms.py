from catalogs.models import (
    Organization,
    Department,
    Storage,
    Device,
    Product,
    Line,
    TypeFactoryOperation
)

from django.forms import ModelForm


class TypeFactoryOperationForm(ModelForm):
    class Meta:
        model = TypeFactoryOperation
        exclude = ['guid']


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
