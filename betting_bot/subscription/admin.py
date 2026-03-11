from django.contrib import admin
from django.utils.html import format_html
from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user_info',
        'phone_number',
        'package',
        'start_date',
        'end_date',
        'is_active',
    )
    list_filter = ('is_active', 'package')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('start_date', 'end_date', 'created_at')
    
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
    
    def phone_number(self, obj):
        try:
            # Get the most recent successful payment for this user
            from payments.models import Payment
            payment = Payment.objects.filter(
                user=obj.user,
                status=Payment.STATUS_SUCCESS
            ).order_by('-created_at').first()
            return payment.phone if payment else 'N/A'
        except:
            return 'N/A'
    phone_number.short_description = 'Phone Number'
