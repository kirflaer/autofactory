from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView


class PalletListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = '-date'
    model = Task
    template_name = 'tasks.html'
    extra_context = {
        'title': 'Задания',
    }
