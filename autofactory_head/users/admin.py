from django.contrib import admin

from .models import User, Setting


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'settings', 'line', 'role', 'scanner')


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('type_marking_close',)


admin.site.register(Setting, SettingsAdmin)
admin.site.register(User, UserAdmin)
