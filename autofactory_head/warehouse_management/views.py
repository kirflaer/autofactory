from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from warehouse_management.models import Pallet


class PalletListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = '-date'
    model = Pallet
    template_name = 'pallet.html'
    extra_context = {
        'title': 'Собранные паллеты',
    }
