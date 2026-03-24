from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.urls import path
from django.shortcuts import render
from .models import (
    PaymentProvider,
    PaymentProviderConfig,
    YooPaymentProvider,
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


@admin.register(YooPaymentProvider)
class YooPaymentProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "environment", "is_active", "updated_at")
    list_editable = ("is_active",)
    fieldsets = (
        ("Credentials", {"fields": ("name", "api_username", "api_password", "environment")}),
        ("Endpoints", {"fields": ("primary_url", "backup_url")}),
        ("Webhooks", {"fields": ("notification_url", "failure_url")}),
        ("Status", {"fields": ("is_active",)}),
    )


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
    actions = ["mark_as_failed", "mark_as_success"]

    def get_urls(self):
        urls = super().get_urls()
        custom = [path("dashboard/", self.admin_site.admin_view(self.dashboard_view), name="payments_dashboard")]
        return custom + urls

    def dashboard_view(self, request):
        today = timezone.now().date()
        this_month_start = today.replace(day=1)

        qs = Payment.objects.filter(status=Payment.STATUS_SUCCESS)

        total_revenue = qs.aggregate(t=Sum("amount"))["t"] or 0
        today_revenue = qs.filter(created_at__date=today).aggregate(t=Sum("amount"))["t"] or 0
        month_revenue = qs.filter(created_at__date__gte=this_month_start).aggregate(t=Sum("amount"))["t"] or 0
        total_payments = qs.count()
        failed_payments = Payment.objects.filter(status=Payment.STATUS_FAILED).count()
        pending_payments = Payment.objects.filter(status=Payment.STATUS_PENDING).count()

        from subscription.models import Subscription
        active_subscribers = Subscription.objects.filter(is_active=True).count()
        new_today = Subscription.objects.filter(created_at__date=today).count()
        new_this_month = Subscription.objects.filter(created_at__date__gte=this_month_start).count()

        # Revenue per package
        per_package = (
            qs.values("package__name")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        # Last 7 days daily revenue
        from django.db.models.functions import TruncDate
        daily = (
            qs.filter(created_at__date__gte=today - timezone.timedelta(days=6))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("day")
        )

        context = {
            **self.admin_site.each_context(request),
            "title": "Revenue Dashboard",
            "total_revenue": total_revenue,
            "today_revenue": today_revenue,
            "month_revenue": month_revenue,
            "total_payments": total_payments,
            "failed_payments": failed_payments,
            "pending_payments": pending_payments,
            "active_subscribers": active_subscribers,
            "new_today": new_today,
            "new_this_month": new_this_month,
            "per_package": per_package,
            "daily": daily,
        }
        return render(request, "admin/payments_dashboard.html", context)

    def mark_as_failed(self, request, queryset):
        updated = queryset.filter(status=Payment.STATUS_PENDING).update(status=Payment.STATUS_FAILED)
        self.message_user(request, f"{updated} payment(s) marked as FAILED.", messages.WARNING)
    mark_as_failed.short_description = "Mark selected as FAILED"

    def mark_as_success(self, request, queryset):
        count = 0
        for payment in queryset.filter(status=Payment.STATUS_PENDING):
            try:
                from .services import confirm_payment
                confirm_payment(reference=payment.reference)
                count += 1
            except Exception as e:
                self.message_user(request, f"Error on {payment.reference}: {e}", messages.ERROR)
        self.message_user(request, f"{count} payment(s) confirmed as SUCCESS.", messages.SUCCESS)
    mark_as_success.short_description = "Mark selected as SUCCESS (creates subscription)"

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
