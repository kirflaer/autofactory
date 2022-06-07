from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from tasks.models import Task


class TaskListView(LoginRequiredMixin, ListView):
    context_object_name = 'data'
    ordering = '-date'
    model = Task
    template_name = 'tasks.html'
    extra_context = {
        'title': 'Задания',
    }
