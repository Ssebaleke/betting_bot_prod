from django.contrib import admin
from .models import TelegramBotConfig, TelegramProfile


@admin.register(TelegramBotConfig)
class TelegramBotConfigAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_editable = ("is_active",)
    search_fields = ("name",)

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            TelegramBotConfig.objects.exclude(
                id=obj.id
            ).update(is_active=False)
        super().save_model(request, obj, form, change)


@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_id", "username", "linked_at")
    search_fields = ("user__username", "telegram_id")
