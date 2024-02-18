from django import forms
from django.utils.translation import gettext_lazy as _
from django_select2 import forms as s2forms

from warehouse_management.models import (
    PalletProduct,
    Pallet,
    PalletCollectOperation,
    OperationPallet,
    StorageCellContentState,
    StorageCell,
    SelectionOperation,
    OrderOperation,
    ShipmentOperation,
    CancelShipmentOperation,
    MovementBetweenCellsOperation,
    AcceptanceOperation,
    PlacementToCellsOperation,
    WriteOffOperation,
)


class FlagWidget(forms.ModelForm):

    unloaded = forms.BooleanField(
        label=_('Выгружена'),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input'
            }
        )
    )

    ready_to_unload = forms.BooleanField(
        label=_('Готова к выгрузке'),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input'
            }
        )
    )

    closed = forms.BooleanField(
        label=_('Закрыта'),
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input'
            }
        )
    )


class PalletProductForm(forms.ModelForm):
    class Meta:
        model = PalletProduct
        fields = ('is_collected',)


class PalletForm(forms.ModelForm):

    class Meta:
        model = Pallet
        fields = ('product', 'status', 'weight', 'content_count', 'batch_number', 'production_date')


class PalletCollectOperationForm(forms.ModelForm):

    class Meta:
        model = PalletCollectOperation
        fields = ('status', 'unloaded', 'ready_to_unload', 'closed')


class OperationPalletForm(forms.ModelForm):

    pallet = forms.ModelChoiceField(
        queryset=Pallet.objects.all(),
        required=False,
        widget=s2forms.ModelSelect2Widget(
            model=Pallet,
            search_fields=['guid__icontains', 'id__startswith'],
            attrs={
                'class': 'form-select',
                'data-placeholder': '',
                'data-minimum-input-length': '2',
                'data-allow-clear': 'true',
            },
            max_results=50
        ),
        label='Паллета'
    )

    class Meta:
        model = OperationPallet
        fields = ('pallet',)


class StorageCellContentStateForm(forms.ModelForm):

    cell = forms.ModelChoiceField(
        queryset=StorageCell.objects.all(),
        widget=s2forms.ModelSelect2Widget(
            model=StorageCell,
            search_fields=['guid__icontains', 'name__startswith'],
            attrs={
                'class': 'form-select',
                'data-placeholder': '',
                'data-allow-clear': 'true'
            },
            max_results=50
        ),
        label='Ячейка'
    )

    class Meta:
        model = StorageCellContentState
        fields = ('cell',)


class SelectionOperationForm(FlagWidget):

    class Meta:
        model = SelectionOperation
        fields = ('unloaded', 'ready_to_unload', 'closed')


class OrderOperationForm(FlagWidget):

    class Meta:
        model = OrderOperation
        fields = ('unloaded', 'ready_to_unload', 'closed')


class ShipmentOperationForm(FlagWidget):

    class Meta:
        model = ShipmentOperation
        fields = ('unloaded', 'ready_to_unload', 'closed')


class CancelShipmentOperationForm(FlagWidget):

    class Meta:
        model = CancelShipmentOperation
        fields = ('unloaded', 'ready_to_unload', 'closed')


class MovementBetweenCellsForm(FlagWidget):

    class Meta:
        model = MovementBetweenCellsOperation
        fields = ('unloaded', 'ready_to_unload', 'closed')


class AcceptanceOperationForm(FlagWidget):

    class Meta:
        model = AcceptanceOperation
        fields = ('unloaded', 'ready_to_unload', 'closed')


class PlacementToCellsOperationForm(FlagWidget):

    class Meta:
        model = PlacementToCellsOperation
        fields = ('unloaded', 'ready_to_unload', 'closed')


class WriteOffOperationForm(FlagWidget):

    class Meta:
        model = WriteOffOperation
        fields = ('unloaded', 'ready_to_unload', 'closed')
