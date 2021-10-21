from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from catalogs.models import (
    Organization,
    Department,
    Storage,
    Device,
    Product,
    Line
)

from packing.models import (
    MarkingOperation,
    MarkingOperationMarks
)
from django.urls import reverse_lazy

from django.views.generic import (
    ListView,
    CreateView,
    DeleteView,
    UpdateView
)

from .forms import (
    ProductForm,
    LineForm,
    DepartmentForm,
    DeviceForm,
    OrganizationForm,
    StorageForm,
   # ShiftOperationForm
)

from django.contrib.auth.mixins import LoginRequiredMixin


@login_required
def index(request):
    return render(request, 'index.html')


class CatalogBasicListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = 'name'
    template_name = 'catalogs\external_catalogs_list.html'

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


class OperationBasicListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = 'date'


class MarkingOperationListView(OperationBasicListView):
    model = MarkingOperation
    template_name = 'operation\marking.html'
    extra_context = {
        'title': 'Маркировка',
        'element_new_link': 'organization_new',
    }


class MarkingOperationRemoveView(CatalogBasicRemoveView):
    model = MarkingOperation
    success_url = reverse_lazy('marking')


class MarkRemoveView(CatalogBasicRemoveView):
    model = MarkingOperationMarks
    success_url = reverse_lazy('marking')


# class ShiftOperationListView(OperationBasicListView):
#     model = ShiftOperation
#     template_name = 'operation\shift.html'
#     extra_context = {
#         'title': 'Смены',
#         'element_new_link': 'organization_new',
#     }
#
#
# class ShiftOperationUpdateView(CatalogBasicUpdateView):
#     model = ShiftOperation
#     form_class = ShiftOperationForm
#     success_url = reverse_lazy('shift')
#
#
# class ShiftOperationRemoveView(CatalogBasicRemoveView):
#     model = ShiftOperation
#     success_url = reverse_lazy('shift')


class OrganizationListView(CatalogBasicListView):
    model = Organization
    extra_context = {
        'title': 'Организации',
        'element_new_link': 'organization_new',
        'catalog_edit_link': 'organization_edit',
        'catalog_remove_link': 'organization_remove'
    }


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


class ProductListView(CatalogBasicListView):
    model = Product
    template_name = 'catalogs\products.html'
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
    template_name = 'catalogs\lines.html'
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
    template_name = 'catalogs\devices.html'
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
    success_url = reverse_lazy('lines')


class DeviceRemoveView(CatalogBasicRemoveView):
    model = Device
    success_url = reverse_lazy('devices')


@login_required
def marking_detail(request, pk):
    operation = get_object_or_404(MarkingOperation, pk=pk)
    marks = MarkingOperationMarks.objects.all().filter(operation=operation)
    return render(request, 'operation\marking_detail.html', {'data': marks})
