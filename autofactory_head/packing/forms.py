from django.forms import ModelForm

from packing.models import MarkingOperation


class MarkingOperationForm(ModelForm):
    class Meta:
        model = MarkingOperation
        fields = ['unloaded', 'ready_to_unload']
