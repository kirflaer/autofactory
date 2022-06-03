from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
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

#
# @login_required
# def pallet_detail(request, pk):
#     pallet = get_object_or_404(Pallet, pk=pk)
#     codes = PalletCode.objects.all().filter(pallet=pallet)
#     return render(request, 'pallet_codes.html', {'data': codes})
#
#
