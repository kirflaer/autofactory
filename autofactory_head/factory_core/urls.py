from django.urls import path

from . import views

from .views import (
    OrganizationListView,
    LineListView,
    DepartmentListView,
    StorageListView,
    ProductListView,
    DeviceListView,
    OrganizationCreateView,
    DeviceCreateView,
    ProductCreateView,
    DepartmentCreateView,
    LineCreateView,
    StorageCreateView,
    ProductRemoveView,
    ProductUpdateView,
    LineRemoveView,
    LineUpdateView,
    StorageUpdateView,
    StorageRemoveView,
    DepartmentRemoveView,
    DepartmentUpdateView,
    DeviceRemoveView,
    DeviceUpdateView,
    OrganizationRemoveView,
    OrganizationUpdateView,
    MarkingOperationListView,
    MarkingOperationRemoveView,
    MarkRemoveView,
    TypeFactoryOperationCreateView,
    TypeFactoryOperationListView,
    TypeFactoryOperationRemoveView,
    TypeFactoryOperationUpdateView,

)

urlpatterns = [
    path('', views.index, name='index'),

    path('organizations/', OrganizationListView.as_view(),
         name='organizations'),
    path('organizations/new/', OrganizationCreateView.as_view(),
         name='organization_new'),
    path('organizations/edit/<uuid:pk>', OrganizationUpdateView.as_view(),
         name='organization_edit'),
    path('organizations/remove/<uuid:pk>', OrganizationRemoveView.as_view(),
         name='organization_remove'),

    path('lines/', LineListView.as_view(), name='lines'),
    path('lines/new/', LineCreateView.as_view(),
         name='line_new'),
    path('lines/edit/<uuid:pk>', LineUpdateView.as_view(),
         name='line_edit'),
    path('lines/remove/<uuid:pk>', LineRemoveView.as_view(),
         name='line_remove'),

    path('products/', ProductListView.as_view(), name='products'),
    path('products/new/', ProductCreateView.as_view(),
         name='product_new'),
    path('products/edit/<uuid:pk>', ProductUpdateView.as_view(),
         name='product_edit'),
    path('products/remove/<uuid:pk>', ProductRemoveView.as_view(),
         name='product_remove'),

    path('storages/', StorageListView.as_view(), name='storages'),
    path('storages/new/', StorageCreateView.as_view(),
         name='storage_new'),
    path('storages/edit/<uuid:pk>', StorageUpdateView.as_view(),
         name='storage_edit'),
    path('storages/remove/<uuid:pk>', StorageRemoveView.as_view(),
         name='storage_remove'),

    path('departments/', DepartmentListView.as_view(), name='departments'),
    path('departments/new/', DepartmentCreateView.as_view(),
         name='department_new'),
    path('departments/edit/<uuid:pk>', DepartmentUpdateView.as_view(),
         name='department_edit'),
    path('departments/remove/<uuid:pk>', DepartmentRemoveView.as_view(),
         name='department_remove'),

    path('devices/', DeviceListView.as_view(), name='devices'),
    path('devices/new/', DeviceCreateView.as_view(),
         name='device_new'),
    path('devices/edit/<uuid:pk>', DeviceUpdateView.as_view(),
         name='device_edit'),
    path('devices/remove/<uuid:pk>', DeviceRemoveView.as_view(),
         name='device_remove'),

    path('type_factory_operation/', TypeFactoryOperationListView.as_view(),
         name='type_factory_operation'),
    path('type_factory_operation/new/',
         TypeFactoryOperationCreateView.as_view(),
         name='type_factory_operation_new'),
    path('type_factory_operation/edit/<int:pk>',
         TypeFactoryOperationUpdateView.as_view(),
         name='type_factory_operation_edit'),
    path('type_factory_operation/remove/<int:pk>',
         TypeFactoryOperationRemoveView.as_view(),
         name='type_factory_operation_remove'),

    path('marking/', MarkingOperationListView.as_view(), name='marking'),
    path('marking/detail/<uuid:pk>', views.marking_detail,
         name='marking_detail'),
    path('marking/remove/<uuid:pk>', MarkingOperationRemoveView.as_view(),
         name='marking_remove'),
    path('marking/remove-mark/<int:pk>', MarkRemoveView.as_view(),
         name='mark-remove'),

]
