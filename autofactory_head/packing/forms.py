from django.forms import ModelForm, DateInput, CharField

from factory_core.models import Shift
from packing.models import MarkingOperation


class MarkingOperationForm(ModelForm):
    class Meta:
        model = MarkingOperation
        fields = ['unloaded', 'ready_to_unload']


class DateCustomInput(DateInput):
    input_type = "date"


class ShiftForm(ModelForm):
    production_date = CharField(label='Дата выработки', widget=DateCustomInput())

    class Meta:
        model = Shift
        fields = ['line', 'batch_number', 'production_date', 'product', 'organization']
