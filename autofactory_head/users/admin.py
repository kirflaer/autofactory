from django.contrib import admin

from .models import User, Setting, ConfigEvent, UserMode, UIElement, UserElement


@admin.action(description='Установить уровень логирования INFO')
def make_log_level_info(model, request, queryset):
    queryset.update(log_level='INFO')


@admin.action(description='Установить уровень логирования ERROR')
def make_log_level_error(model, request, queryset):
    queryset.update(log_level='ERROR')


class UserModeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class ModeUIAdmin(admin.ModelAdmin):
    list_display = ('mode', 'element')


class UIElementAdmin(admin.ModelAdmin):
    list_display = ('name', 'identifier')


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'settings', 'line', 'role', 'scanner', 'device', 'is_superuser', 'log_level')
    list_filter = ('role',)
    actions = [make_log_level_info, make_log_level_error]


class ConfigEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'type_event', 'argument')


class SettingsAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'type_marking_close', 'collect_pallet_mode_is_active')


admin.site.register(Setting, SettingsAdmin)
admin.site.register(UserElement, ModeUIAdmin)
admin.site.register(UIElement, UIElementAdmin)
admin.site.register(UserMode, UserModeAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(ConfigEvent, ConfigEventAdmin)
