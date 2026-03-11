from django.contrib import admin
from django.utils.html import format_html
from .models import (
    PaymentProvider,
    PaymentProviderConfig,
    Payment,
)


@admin.register(PaymentProvider)
class PaymentProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "base_url", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name",)


@admin.register(PaymentProviderConfig)
class PaymentProviderConfigAdmin(admin.ModelAdmin):
    list_display = ("provider", "is_active")
    list_editable = ("is_active",)
    readonly_fields = ("provider",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "user_info",
        "package",
        "phone",
        "amount",
        "colored_status",
        "created_at",
    )
    list_filter = ("status", "provider", "created_at")
    search_fields = ("reference", "phone", "user__username")
    readonly_fields = ("reference", "created_at")
    
    def user_info(self, obj):
        try:
            telegram_profile = obj.user.telegramprofile
            telegram_username = telegram_profile.username or 'N/A'
            return format_html(
                '<strong>{}</strong><br/><small>@{}</small>',
                obj.user.username,
                telegram_username
            )
        except:
            return obj.user.username
    user_info.short_description = 'User'
    
    def colored_status(self, obj):
        colors = {
            Payment.STATUS_SUCCESS: 'green',
            Payment.STATUS_FAILED: 'red',
            Payment.STATUS_PENDING: 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    colored_status.short_description = 'Status'
