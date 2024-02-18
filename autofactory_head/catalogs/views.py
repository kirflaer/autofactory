from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from catalogs.models import (Department, Device, Line, Organization, Product,
                             Storage, TypeFactoryOperation, Unit, LineProduct)

from .forms import (CustomUserForm, DepartmentForm, DeviceForm, LineForm,
                    OrganizationForm, ProductForm, StorageForm,
                    TypeFactoryOperationForm, UnitForm, LineProductForm)

User = get_user_model()


class CatalogBasicListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = 'name'
    template_name = 'base_catalogs_list.html'
    paginate_by = 50

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data['list_collapse'] = False
        data['possibility_of_adding'] = True
        return data


class CatalogBasicCreateView(LoginRequiredMixin, CreateView):
    template_name = 'new_base.html'


class CatalogBasicUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'new_base.html'


class CatalogBasicRemoveView(LoginRequiredMixin, DeleteView):
    template_name = 'confirm_base.html'


class OrganizationListView(CatalogBasicListView):
    model = Organization
    extra_context = {
        'title': 'Организации',
        'element_new_link': 'organization_new',
        'catalog_edit_link': 'organization_edit',
        'catalog_remove_link': 'organization_remove'
    }


class UserListView(LoginRequiredMixin, ListView):
    model = User
    context_object_name = 'data'
    ordering = 'username'
    template_name = 'users.html'
    extra_context = {
        'title': 'Пользователи',
        'element_new_link': 'users_new',
        'catalog_edit_link': 'users_edit',
        'catalog_remove_link': 'users_remove'
    }

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data['possibility_of_adding'] = True
        return data

    def get_queryset(self):
        queryset = User.objects.all()
        queryset = queryset.filter(is_superuser=False, is_active=True)
        return queryset


class UserCreateView(CatalogBasicCreateView):
    model = User
    form_class = CustomUserForm
    success_url = reverse_lazy('users')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(self.request.POST['password_custom'])
        user.settings = self.request.user.settings
        user.save()
        return super().form_valid(form)


class UserUpdateView(CatalogBasicUpdateView):
    model = User
    form_class = CustomUserForm
    success_url = reverse_lazy('users')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(self.request.POST['password_custom'])
        user.save()
        return HttpResponseRedirect(self.get_success_url())


class UserRemoveView(CatalogBasicRemoveView):
    model = User
    success_url = reverse_lazy('users')


class OrganizationCreateView(CatalogBasicCreateView):
    model = Organization
    form_class = OrganizationForm
    success_url = reverse_lazy('organizations')


class OrganizationUpdateView(CatalogBasicUpdateView):
    model = Organization
    form_class = OrganizationForm
    success_url = reverse_lazy('organizations')


class OrganizationRemoveView(CatalogBasicRemoveView):
    model = Organization
    success_url = reverse_lazy('organizations')


class UnitListView(CatalogBasicListView):
    model = Unit
    template_name = 'product_detail.html'
    extra_context = {
        'title': 'Упаковки',
        'element_new_link': 'unit_new',
        'catalog_edit_link': 'unit_edit',
        'catalog_remove_link': 'unit_remove'
    }

    def get_queryset(self):
        product = get_object_or_404(Product, guid=self.kwargs['pk'])
        return Unit.objects.all().filter(product=product)

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data['possibility_of_adding'] = True
        data['product_uuid'] = self.kwargs['pk']
        return data


class UnitCreateView(CatalogBasicCreateView):
    model = Unit
    form_class = UnitForm

    def get_success_url(self):
        return reverse_lazy('product_detail',
                            kwargs={'pk': self.kwargs['pk']})

    def form_valid(self, form):
        product = get_object_or_404(Product, guid=self.kwargs['pk'])
        unit = form.save(commit=False)
        unit.product = product
        unit.save()
        return HttpResponseRedirect(self.get_success_url())


class UnitUpdateView(CatalogBasicUpdateView):
    model = Unit
    form_class = UnitForm

    def get_success_url(self):
        return reverse_lazy('product_detail',
                            kwargs={'pk': self.object.product.guid})


class UnitRemoveView(CatalogBasicRemoveView):
    model = Unit

    def get_success_url(self):
        return reverse_lazy('product_detail',
                            kwargs={'pk': self.object.product.guid})


class ProductListView(CatalogBasicListView):
    model = Product
    template_name = 'products.html'
    extra_context = {
        'title': 'Номенклатура',
        'element_new_link': 'product_new',
        'catalog_edit_link': 'product_edit',
        'catalog_remove_link': 'product_remove'
    }


class ProductCreateView(CatalogBasicCreateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('products')


class ProductUpdateView(CatalogBasicUpdateView):
    model = Product
    form_class = ProductForm
    success_url = reverse_lazy('products')


class ProductRemoveView(CatalogBasicRemoveView):
    model = Product
    success_url = reverse_lazy('products')


class StorageListView(CatalogBasicListView):
    model = Storage
    extra_context = {
        'title': 'Склады',
        'element_new_link': 'storage_new',
        'catalog_edit_link': 'storage_edit',
        'catalog_remove_link': 'storage_remove'
    }


class StorageCreateView(CatalogBasicCreateView):
    model = Storage
    form_class = StorageForm
    success_url = reverse_lazy('storages')


class StorageUpdateView(CatalogBasicUpdateView):
    model = Storage
    form_class = StorageForm
    success_url = reverse_lazy('storages')


class StorageRemoveView(CatalogBasicRemoveView):
    model = Storage
    success_url = reverse_lazy('storages')


class DepartmentListView(CatalogBasicListView):
    model = Department
    extra_context = {
        'title': 'Подразделения',
        'element_new_link': 'department_new',
        'catalog_edit_link': 'department_edit',
        'catalog_remove_link': 'department_remove'
    }


class DepartmentCreateView(CatalogBasicCreateView):
    model = Department
    form_class = DepartmentForm
    success_url = reverse_lazy('departments')


class DepartmentUpdateView(CatalogBasicUpdateView):
    model = Department
    form_class = DepartmentForm
    success_url = reverse_lazy('departments')


class DepartmentRemoveView(CatalogBasicRemoveView):
    model = Department
    success_url = reverse_lazy('departments')


class LineListView(CatalogBasicListView):
    model = Line
    template_name = 'lines.html'
    extra_context = {
        'title': 'Линии',
        'element_new_link': 'line_new',
        'catalog_edit_link': 'line_edit',
        'catalog_remove_link': 'line_remove'
    }


class LineCreateView(CatalogBasicCreateView):
    model = Line
    form_class = LineForm
    success_url = reverse_lazy('lines')


class LineUpdateView(CatalogBasicUpdateView):
    model = Line
    form_class = LineForm
    success_url = reverse_lazy('lines')


class LineRemoveView(CatalogBasicRemoveView):
    model = Line
    success_url = reverse_lazy('lines')


class DeviceListView(CatalogBasicListView):
    model = Device
    template_name = 'devices.html'
    extra_context = {
        'title': 'Устройства сбора данных',
        'element_new_link': 'device_new',
        'catalog_edit_link': 'device_edit',
        'catalog_remove_link': 'device_remove'
    }


class DeviceCreateView(CatalogBasicCreateView):
    model = Device
    form_class = DeviceForm
    success_url = reverse_lazy('devices')


class DeviceUpdateView(CatalogBasicUpdateView):
    model = Device
    form_class = DeviceForm
    success_url = reverse_lazy('devices')


class DeviceRemoveView(CatalogBasicRemoveView):
    model = Device
    success_url = reverse_lazy('devices')


class TypeFactoryOperationListView(CatalogBasicListView):
    model = TypeFactoryOperation
    template_name = 'operation_factory_type.html'
    extra_context = {
        'title': 'Типы производственных операций',
        'element_new_link': 'type_factory_operation_new',
        'catalog_edit_link': 'type_factory_operation_edit',
        'catalog_remove_link': 'type_factory_operation_remove'
    }


class TypeFactoryOperationCreateView(CatalogBasicCreateView):
    model = TypeFactoryOperation
    form_class = TypeFactoryOperationForm
    success_url = reverse_lazy('type_factory_operation')


class TypeFactoryOperationUpdateView(CatalogBasicUpdateView):
    model = TypeFactoryOperation
    form_class = TypeFactoryOperationForm
    success_url = reverse_lazy('type_factory_operation')


class TypeFactoryOperationRemoveView(CatalogBasicRemoveView):
    model = TypeFactoryOperation
    success_url = reverse_lazy('type_factory_operation')


class LineProductListView(CatalogBasicListView):

    model = LineProduct
    template_name = 'line_product.html'
    ordering = '-id'
    extra_context = {
        'title': 'Номенклатура линии',
        'element_new_link': 'line_product_new'
    }


class LineProductCreateView(CatalogBasicCreateView):

    model = LineProduct
    template_name = 'line_product_new.html'
    form_class = LineProductForm
    success_url = reverse_lazy('line-product')
