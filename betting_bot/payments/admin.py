from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from django.urls import path
from django.shortcuts import render
from .models import (
    SMSConfig,
    SMSBalance,
    SMSTopUp,
    PaymentProvider,
    PaymentProviderConfig,
    YooPaymentProvider,
    Payment,
)


@admin.register(SMSConfig)
class SMSConfigAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_active", "created_at")
    list_editable = ("is_active",)
    fieldsets = (
        ("UGSMS v2 Credentials", {"fields": ("api_key",)}),
        ("Status", {"fields": ("is_active",)}),
    )


@admin.register(SMSBalance)
class SMSBalanceAdmin(admin.ModelAdmin):
    list_display = ("credits", "price_per_sms", "updated_at")
    readonly_fields = ("credits", "updated_at")
    fieldsets = (
        ("💰 SMS Pricing (Set by Super Admin)", {
            "description": "Set the price per SMS credit charged to the owner. The owner pays this amount per SMS sent to subscribers.",
            "fields": ("price_per_sms",),
        }),
        ("📊 Current Balance (Auto-managed)", {
            "description": "Credits are added automatically when the owner tops up via Mobile Money. Do not edit manually.",
            "fields": ("credits", "updated_at"),
        }),
    )

    def has_add_permission(self, request):
        return not SMSBalance.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [path("topup/", self.admin_site.admin_view(self.topup_view), name="smsbalance_topup")]
        return custom + urls

    def topup_view(self, request):
        from django.shortcuts import redirect
        if request.method == "POST":
            try:
                credits = int(request.POST.get("credits", 0))
                note = request.POST.get("note", "Manual top-up by super admin").strip()
                if credits <= 0:
                    raise ValueError("Credits must be a positive number.")
                balance = SMSBalance.get()
                balance.credits += credits
                balance.save(update_fields=["credits", "updated_at"])
                # Log it as an SMSTopUp record
                import uuid
                SMSTopUp.objects.create(
                    phone="admin",
                    amount_paid=0,
                    credits_added=credits,
                    payment_reference=f"manual-{uuid.uuid4().hex[:12]}",
                    status=SMSTopUp.STATUS_SUCCESS,
                )
                self.message_user(request, f"✅ Successfully added {credits} SMS credits. New balance: {balance.credits}.", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"❌ Error: {e}", messages.ERROR)
            return redirect("../")

        balance = SMSBalance.get()
        topups = SMSTopUp.objects.order_by("-created_at")[:15]
        context = {
            **self.admin_site.each_context(request),
            "title": "Manual SMS Top-Up",
            "balance": balance,
            "topups": topups,
            "opts": self.model._meta,
        }
        return render(request, "admin/sms_topup.html", context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["topup_url"] = "../topup/"
        extra_context["show_topup_button"] = True
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(SMSTopUp)
class SMSTopUpAdmin(admin.ModelAdmin):
    list_display = ("phone", "amount_paid", "credits_added", "status", "created_at")
    readonly_fields = ("phone", "amount_paid", "credits_added", "payment_reference", "status", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
