from django import forms

from factory_core.models import Shift
from packing.models import MarkingOperation


class MarkingOperationForm(forms.ModelForm):
    class Meta:
        model = MarkingOperation
        fields = ['unloaded', 'ready_to_unload', 'closed']


class DateCustomInput(forms.DateInput):
    input_type = "date"


class ShiftForm(forms.ModelForm):

    production_date = forms.CharField(label='Дата выработки', widget=DateCustomInput())

    class Meta:
        model = Shift
        fields = ('line', 'batch_number', 'production_date', 'product', 'organization', 'type', 'closed')
