from django.urls import path

from .views import (
    ShipmentListView, OrderListView, OrderDetailListView, SourceRemoveView, SourceListView, PalletProductUpdateView,
    PalletShipmentListView, PalletDetailView, PalletListView, PalletUpdateView, PalletOperationListView,
    PalletCollectOperationListView, PalletCollectOperationUpdateView, StorageCellContentStateListView,
    StorageCellContentStateUpdateView, StorageCellContentStateDeleteView, SelectionOperationListView,
    SelectionOperationUpdateView, SelectionOperationDeleteView, OrderOperationListView, OrderOperationUpdateView,
    OrderOperationDeleteView, ShipmentOperationUpdateView, ShipmentOperationDeleteView, CancelShipmentOperationListView,
    CancelShipmentOperationUpdateView, CancelShipmentOperationDeleteView, MovementBetweenCellsListView,
    MovementBetweenCellsUpdateView, MovementBetweenCellsDeleteView, AcceptanceOperationListView,
    AcceptanceOperationUpdateView, AcceptanceOperationDeleteView, PlacementToCellsOperationListView,
    PlacementToCellsOperationUpdateView, PlacementToCellsOperationDeleteView, WriteOffOperationListView,
    WriteOffOperationUpdateView, WriteOffOperationDeleteView,
)

urlpatterns = [
    path('shipment/', ShipmentListView.as_view(), name='shipment'),
    path('shipment/edit/<uuid:pk>/', ShipmentOperationUpdateView.as_view(), name='shipment_operation_edit'),
    path('shipment/delete/<uuid:pk>/', ShipmentOperationDeleteView.as_view(), name='shipment_operation_delete'),
    path('shipment/pallets/<uuid:parent_task>', PalletShipmentListView.as_view(), name='shipment_pallets'),
    path('shipment/pallets/detail/<uuid:pallet>', PalletDetailView.as_view(), name='shipment_pallets_detail'),
    path('shipment/orders/<uuid:parent_task>/', OrderListView.as_view(), name='orders'),
    path('orders/', OrderOperationListView.as_view(), name='order_operation_list'),
    path('orders/edit/<uuid:pk>/', OrderOperationUpdateView.as_view(), name='order_operation_edit'),
    path('orders/delete/<uuid:pk>/', OrderOperationDeleteView.as_view(), name='order_operation_delete'),
    path('orders/products/<uuid:order>/', OrderDetailListView.as_view(), name='orders_detail'),
    path('orders/products/edit/<int:pk>/', PalletProductUpdateView.as_view(), name='orders_products_update'),
    path('sources/<uuid:key>/', SourceListView.as_view(), name='sources'),
    path('sources/remove/<int:pk>/', SourceRemoveView.as_view(), name='sources_remove'),
    path('pallets/', PalletListView.as_view(), name='pallets_list'),
    path('pallets/edit/<uuid:pk>/', PalletUpdateView.as_view(), name='pallet_detail'),
    path('pallet-operations/', PalletOperationListView.as_view(), name='pallet_operations'),
    path('pallet-collect-operations/', PalletCollectOperationListView.as_view(), name='pallet_collect_operation_list'),
    path(
        'pallet-collect-operations/edit/<uuid:pk>/',
        PalletCollectOperationUpdateView.as_view(),
        name='pallet_collect_operation_edit'
    ),
    path(
        'storage-cell-content-state/',
        StorageCellContentStateListView.as_view(),
        name='storage_cell_content_state_list'
    ),
    path(
        'storage-cell-content-state/edit/<int:pk>/',
        StorageCellContentStateUpdateView.as_view(),
        name='storage_cell_content_state_edit'
    ),
    path(
        'storage-cell-content-state/delete/<int:pk>/',
        StorageCellContentStateDeleteView.as_view(),
        name='storage_cell_content_state_delete'
    ),
    path('selection-operations/', SelectionOperationListView.as_view(), name='selection_operation_list'),
    path(
        'selection-operations/edit/<uuid:pk>/',
        SelectionOperationUpdateView.as_view(),
        name='selection_operation_edit'
    ),
    path(
        'selection-operations/delete/<uuid:pk>/',
        SelectionOperationDeleteView.as_view(),
        name='selection_operation_delete'
    ),
    path(
        'cancel-shipment-operations/',
        CancelShipmentOperationListView.as_view(),
        name='cancel_shipment_operation_list'
    ),
    path(
        'cancel-shipment-operations/edit/<uuid:pk>/',
        CancelShipmentOperationUpdateView.as_view(),
        name='cancel_shipment_operation_edit'
    ),
    path(
        'cancel-shipment-operations/delete/<uuid:pk>/',
        CancelShipmentOperationDeleteView.as_view(),
        name='cancel_shipment_operation_delete'
    ),
    path('movement-between-cells/', MovementBetweenCellsListView.as_view(), name='movement_between_cells_list'),
    path(
        'movement-between-cells/edit/<uuid:pk>/',
        MovementBetweenCellsUpdateView.as_view(),
        name='movement_between_cells_edit'
    ),
    path(
        'movement-between-cells/delete/<uuid:pk>/',
        MovementBetweenCellsDeleteView.as_view(),
        name='movement_between_cells_delete'
    ),
    path('acceptance-operations/', AcceptanceOperationListView.as_view(), name='acceptance_operation_list'),
    path(
        'acceptance-operations/edit/<uuid:pk>/',
        AcceptanceOperationUpdateView.as_view(),
        name='acceptance_operation_edit'
    ),
    path(
        'acceptance-operations/delete/<uuid:pk>/',
        AcceptanceOperationDeleteView.as_view(),
        name='acceptance_operation_delete'
    ),
    path(
        'placemet-to-cell-operations/',
        PlacementToCellsOperationListView.as_view(),
        name='placement_to_cell_operation_list'
    ),
    path(
        'placemet-to-cell-operations/edit/<uuid:pk>/',
        PlacementToCellsOperationUpdateView.as_view(),
        name='placement_to_cell_operation_edit'
    ),
    path(
        'placemet-to-cell-operations/delete/<uuid:pk>/',
        PlacementToCellsOperationDeleteView.as_view(),
        name='placement_to_cell_operation_delete'
    ),
    path('write-off-operations/', WriteOffOperationListView.as_view(), name='write_off_operation_list'),
    path(
        'write-off-operations/edit/<uuid:pk>/',
        WriteOffOperationUpdateView.as_view(),
        name='write_off_operation_edit'
    ),
    path(
        'write-off-operations/delete/<uuid:pk>/',
        WriteOffOperationDeleteView.as_view(),
        name='write_off_operation_delete'
    ),
]
