from django.contrib import admin

from .models import User, Settings


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'settings')


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('type_marking_close',)


admin.site.register(Settings, SettingsAdmin)
admin.site.register(User, UserAdmin)
