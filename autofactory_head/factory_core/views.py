from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from packing.marking_services import get_dashboard_data
from catalogs.models import (
    Organization,
    Department,
    Storage,
    Device,
    Product,
    Line,
    TypeFactoryOperation,
    Unit,
    Log
)

from packing.models import (
    MarkingOperation,
    MarkingOperationMark,
    CollectingOperation,
    CollectCode
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
    TypeFactoryOperationForm,
    CustomUserForm, UnitForm
)

from .log_services import logs_summary_data, log_line_decode

from django.contrib.auth.mixins import LoginRequiredMixin

User = get_user_model()


@login_required
def index(request):
    dashboard_data = get_dashboard_data()
    dashboard_data['version'] = settings.VERSION
    return render(request, 'index.html', dashboard_data)


class CatalogBasicListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = 'name'
    template_name = 'base_catalogs_list.html'

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
    ordering = '-date'


class MarkingOperationListView(OperationBasicListView):
    model = MarkingOperation
    template_name = 'marking.html'
    extra_context = {
        'title': 'Маркировка',
        'element_new_link': 'organization_new',
    }


class MarkingOperationRemoveView(CatalogBasicRemoveView):
    model = MarkingOperation
    success_url = reverse_lazy('marking')


class MarkRemoveView(CatalogBasicRemoveView):
    model = MarkingOperationMark
    success_url = reverse_lazy('marking')


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
        queryset = queryset.filter(is_superuser=False)
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


@login_required
def marking_detail(request, pk):
    operation = get_object_or_404(MarkingOperation, pk=pk)
    marks = MarkingOperationMark.objects.all().filter(operation=operation)
    return render(request, 'marking_detail.html', {'data': marks})


def check_status_view(request):
    return render(request, 'check_form.html')


class CollectingOperationListView(OperationBasicListView):
    model = CollectingOperation
    template_name = 'collecting.html'
    extra_context = {
        'title': 'Сбор паллет',
    }


@login_required
def collecting_detail(request, pk):
    operation = get_object_or_404(CollectingOperation, pk=pk)
    codes = CollectCode.objects.all().filter(operation=operation)
    return render(request, 'collecting_detail.html', {'data': codes})


class LogListView(LoginRequiredMixin, ListView):
    model = Log
    context_object_name = 'data'
    ordering = '-date'
    template_name = 'log.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        data = super().get_context_data(object_list=object_list, **kwargs)
        data['list_collapse'] = True
        data['possibility_of_adding'] = True
        data['devices'] = Device.objects.all()

        return data


@login_required
def logs_detail(request, pk):
    log = get_object_or_404(Log, pk=pk)
    log_data = log_line_decode(log.data[2:])
    return render(request, 'log_detail.html', {'data': (log_data,)})


@login_required
def logs_summary(request):
    device_guid = request.GET.get('device')
    device = get_object_or_404(Device, pk=device_guid)
    date_source = request.GET.get('date_source')
    return render(request, 'log_detail.html',
                  {'data': logs_summary_data(device, date_source)})
