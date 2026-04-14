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
    LivePayProvider,
    RevenueConfig,
    PlatformWallet,
    OwnerWallet,
    WithdrawalRequest,
    KwaPayProvider,
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
            "description": "Set the price per SMS credit charged to the owner.",
            "fields": ("price_per_sms",),
        }),
        ("📊 Current Balance (Auto-managed)", {
            "description": "Credits are added automatically when the owner tops up via Mobile Money.",
            "fields": ("credits", "updated_at"),
        }),
    )

    def has_add_permission(self, request):
        return not SMSBalance.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom = [path("1/topup/", self.admin_site.admin_view(self.topup_view), name="smsbalance_topup")]
        return custom + urls

    def topup_view(self, request):
        from django.shortcuts import redirect
        if request.method == "POST":
            try:
                credits = int(request.POST.get("credits", 0))
                if credits <= 0:
                    raise ValueError("Credits must be a positive number.")
                balance = SMSBalance.get()
                balance.credits += credits
                balance.save(update_fields=["credits", "updated_at"])
                import uuid
                SMSTopUp.objects.create(
                    phone="admin",
                    amount_paid=0,
                    credits_added=credits,
                    payment_reference=f"manual-{uuid.uuid4().hex[:12]}",
                    status=SMSTopUp.STATUS_SUCCESS,
                )
                self.message_user(request, f"✅ Added {credits} SMS credits. New balance: {balance.credits}.", messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f"❌ Error: {e}", messages.ERROR)
            return redirect("/admin/payments/smsbalance/1/change/")

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
        extra_context["topup_url"] = "/admin/payments/smsbalance/1/topup/"
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

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            LivePayProvider.objects.update(is_active=False)
            from .models import KwaPayProvider
            KwaPayProvider.objects.update(is_active=False)
            YooPaymentProvider.objects.exclude(pk=obj.pk).update(is_active=False)
            self.message_user(request, "✅ Yo! Payments activated. All other providers deactivated.", messages.SUCCESS)
        super().save_model(request, obj, form, change)


@admin.register(LivePayProvider)
class LivePayProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_editable = ("is_active",)
    fieldsets = (
        ("Credentials", {"fields": ("name", "public_key", "secret_key", "transaction_pin", "withdrawal_fee")}),
        ("Status", {"fields": ("is_active",)}),
    )

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            YooPaymentProvider.objects.update(is_active=False)
            from .models import KwaPayProvider
            KwaPayProvider.objects.update(is_active=False)
            LivePayProvider.objects.exclude(pk=obj.pk).update(is_active=False)
            self.message_user(request, "✅ LivePay activated. All other providers deactivated.", messages.SUCCESS)
        super().save_model(request, obj, form, change)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "reference", "user_info", "package", "phone", "amount", "colored_status", "created_at",
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
        per_package = qs.values("package__name").annotate(total=Sum("amount"), count=Count("id")).order_by("-total")
        from django.db.models.functions import TruncDate
        daily = (
            qs.filter(created_at__date__gte=today - timezone.timedelta(days=6))
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("day")
        )
        from payments.models import PlatformWallet, OwnerWallet, RevenueConfig
        platform_wallet = PlatformWallet.get()
        owner_wallet = OwnerWallet.get()
        config = RevenueConfig.get()
        sms_qs = SMSTopUp.objects.filter(status=SMSTopUp.STATUS_SUCCESS)
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
            "platform_balance": platform_wallet.balance,
            "platform_total_earned": platform_wallet.total_earned,
            "owner_balance": owner_wallet.balance,
            "owner_total_earned": owner_wallet.total_earned,
            "commission_percentage": config.percentage,
            "sms_total": sms_qs.aggregate(t=Sum("amount_paid"))["t"] or 0,
            "sms_today": sms_qs.filter(created_at__date=today).aggregate(t=Sum("amount_paid"))["t"] or 0,
            "sms_month": sms_qs.filter(created_at__date__gte=this_month_start).aggregate(t=Sum("amount_paid"))["t"] or 0,
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
            return format_html('<strong>{}</strong><br/><small>@{}</small>', obj.user.username, telegram_profile.username or "N/A")
        except:
            return obj.user.username
    user_info.short_description = "User"

    def colored_status(self, obj):
        colors = {Payment.STATUS_SUCCESS: "green", Payment.STATUS_FAILED: "red", Payment.STATUS_PENDING: "orange"}
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', colors.get(obj.status, "gray"), obj.get_status_display())
    colored_status.short_description = "Status"


@admin.register(RevenueConfig)
class RevenueConfigAdmin(admin.ModelAdmin):
    list_display = ("percentage", "updated_at")
    fieldsets = (
        ("Revenue Settings", {
            "description": "Set the platform revenue percentage deducted from each successful payment.",
            "fields": ("percentage",),
        }),
    )

    def has_add_permission(self, request):
        return not RevenueConfig.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PlatformWallet)
class PlatformWalletAdmin(admin.ModelAdmin):
    list_display = ("balance", "total_earned", "updated_at")
    readonly_fields = ("balance", "total_earned", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OwnerWallet)
class OwnerWalletAdmin(admin.ModelAdmin):
    list_display = ("balance", "total_earned", "updated_at")
    readonly_fields = ("balance", "total_earned", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("amount", "payout_phone", "payout_network", "status", "created_at")
    list_filter = ("status", "payout_network")
    readonly_fields = ("amount", "payout_phone", "payout_network", "status", "failure_reason", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(KwaPayProvider)
class KwaPayProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_editable = ("is_active",)
    fieldsets = (
        ("Credentials", {"fields": ("name", "primary_api", "secondary_api", "callback_url", "withdrawal_fee")}),
        ("Status", {"fields": ("is_active",)}),
    )

    def save_model(self, request, obj, form, change):
        if obj.is_active:
            from .models import YooPaymentProvider, LivePayProvider
            YooPaymentProvider.objects.update(is_active=False)
            LivePayProvider.objects.update(is_active=False)
            KwaPayProvider.objects.exclude(pk=obj.pk).update(is_active=False)
            self.message_user(request, "✅ KwaPay activated. All other providers deactivated.", messages.SUCCESS)
        super().save_model(request, obj, form, change)
