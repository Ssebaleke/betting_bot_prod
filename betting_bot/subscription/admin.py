from django.contrib import admin
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'package',
        'start_date',
        'end_date',
        'is_active',
    )
    list_filter = ('is_active', 'package')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('start_date', 'end_date', 'created_at')
