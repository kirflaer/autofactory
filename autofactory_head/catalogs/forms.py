from django.contrib.auth import get_user_model
from django.forms import CharField, ModelForm, PasswordInput

from catalogs.models import (Department, Device, Line, Organization, Product,
                             Storage, TypeFactoryOperation, Unit, LineProduct)

User = get_user_model()


class TypeFactoryOperationForm(ModelForm):
    class Meta:
        model = TypeFactoryOperation
        exclude = ['guid']


class UnitForm(ModelForm):
    class Meta:
        model = Unit
        exclude = ['guid', 'product', 'external_key']


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


class CustomUserForm(ModelForm):
    password_custom = CharField(label='Пароль', widget=PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'password_custom', 'role', 'line',
                  'vision_controller',
                  'scanner', ]


class StorageForm(ModelForm):
    class Meta:
        model = Storage
        exclude = ['guid']


class DeviceForm(ModelForm):
    class Meta:
        model = Device
        exclude = ['guid', 'activation_code']


class OrganizationForm(ModelForm):
    class Meta:
        model = Organization
        exclude = ['guid']


class LineProductForm(ModelForm):

    class Meta:
        model = LineProduct
        fields = ('line', 'product')
