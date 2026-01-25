from django.contrib import admin
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
        "user",
        "package",
        "phone",
        "amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "provider", "created_at")
    search_fields = ("reference", "phone", "user__username")
    readonly_fields = ("reference", "created_at")
