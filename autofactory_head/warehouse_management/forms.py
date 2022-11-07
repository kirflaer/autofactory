from django.forms import ModelForm

from warehouse_management.models import PalletProduct


class PalletProductForm(ModelForm):
    class Meta:
        model = PalletProduct
        fields = ('is_collected',)
