from django.urls import path

from . import views
from .views import index

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
    MarkingListView
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

    path('marking/', MarkingListView.as_view(), name='marking'),
]
