from django.db import models
from django.contrib.auth.models import User
from packages.models import Package
from decimal import Decimal


class SMSConfig(models.Model):
    api_key = models.CharField(max_length=255, help_text="UGSMS v2 API Key from your UGSMS dashboard")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "SMS Config (UGSMS)"

    def save(self, *args, **kwargs):
        if self.is_active:
            SMSConfig.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"UGSMS – {'ACTIVE' if self.is_active else 'inactive'}"


class SMSBalance(models.Model):
    """Singleton — one row. Tracks owner SMS credits and price set by devs."""
    credits = models.PositiveIntegerField(default=0)
    price_per_sms = models.DecimalField(
        max_digits=8, decimal_places=2, default=0,
        help_text="Price per SMS charged to owner (UGX). Set by developers.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMS Balance"

    def __str__(self):
        return f"{self.credits} credits @ UGX {self.price_per_sms} each"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def deduct(self):
        if self.credits > 0:
            self.credits -= 1
            self.save(update_fields=["credits", "updated_at"])
            return True
        return False


class SMSTopUp(models.Model):
    """Owner self-service top-up via mobile money."""
    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    phone = models.CharField(max_length=20)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    credits_added = models.PositiveIntegerField(default=0)
    payment_reference = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "SMS Top-Up"
        ordering = ["-created_at"]

    def __str__(self):
        return f"+{self.credits_added} credits — {self.status}"


class SMSLog(models.Model):
    STATUS_SENT = "SENT"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [(STATUS_SENT, "Sent"), (STATUS_FAILED, "Failed")]

    phone = models.CharField(max_length=20)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "SMS Log"
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.phone} — {self.status} — {self.sent_at.strftime('%Y-%m-%d %H:%M')}"


class PaymentProvider(models.Model):
    name = models.CharField(max_length=50, unique=True)
    base_url = models.URLField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PaymentProviderConfig(models.Model):
    provider = models.OneToOneField(
        PaymentProvider,
        on_delete=models.CASCADE,
        related_name="config"
    )
    public_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    webhook_url = models.URLField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.provider.name} Config"


class YooPaymentProvider(models.Model):
    SANDBOX = "SANDBOX"
    LIVE = "LIVE"
    ENV_CHOICES = [(SANDBOX, "Sandbox"), (LIVE, "Live")]

    name = models.CharField(max_length=50, default="Yo! Payments")
    api_username = models.CharField(max_length=200)
    api_password = models.CharField(max_length=200)
    environment = models.CharField(max_length=10, choices=ENV_CHOICES, default=LIVE)
    is_active = models.BooleanField(default=False)
    primary_url = models.URLField(default="https://paymentsapi1.yo.co.ug/ybs/task.php")
    backup_url = models.URLField(default="https://paymentsapi2.yo.co.ug/ybs/task.php")
    notification_url = models.URLField(help_text="IPN success webhook URL")
    failure_url = models.URLField(help_text="IPN failure webhook URL")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Yo! Payment Provider"

    def save(self, *args, **kwargs):
        if self.is_active:
            YooPaymentProvider.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.environment})"


class Payment(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    )

    PROVIDER_MAKYPAY = "MAKYPAY"
    PROVIDER_YOO = "YOO"
    PROVIDER_LIVE = "LIVE"
    PROVIDER_TYPE_CHOICES = (
        (PROVIDER_MAKYPAY, "MakyPay"),
        (PROVIDER_YOO, "Yo! Payments"),
        (PROVIDER_LIVE, "LivePay"),
    )

    CHANNEL_TELEGRAM = "TELEGRAM"
    CHANNEL_SMS = "SMS"
    CHANNEL_CHOICES = (
        (CHANNEL_TELEGRAM, "Telegram"),
        (CHANNEL_SMS, "SMS"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    provider = models.ForeignKey(PaymentProvider, on_delete=models.PROTECT, null=True, blank=True)
    provider_type = models.CharField(max_length=10, choices=PROVIDER_TYPE_CHOICES, default=PROVIDER_MAKYPAY)

    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    delivery_channel = models.CharField(
        max_length=10,
        choices=CHANNEL_CHOICES,
        default=CHANNEL_TELEGRAM,
    )

    reference = models.CharField(max_length=100, unique=True)
    external_reference = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} ({self.status})"


class LivePayProvider(models.Model):
    name = models.CharField(max_length=50, default="LivePay")
    public_key = models.CharField(max_length=255)
    secret_key = models.CharField(max_length=255)
    transaction_pin = models.CharField(max_length=20, blank=True, help_text="PIN for Send Money (withdrawals)")
    withdrawal_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00"),
        help_text="Fixed fee added on top of every withdrawal (UGX). Set manually."
    )
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "LivePay Provider"

    def save(self, *args, **kwargs):
        if self.is_active:
            LivePayProvider.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'ACTIVE' if self.is_active else 'inactive'})"


class RevenueConfig(models.Model):
    """Singleton — one row. Controls platform revenue percentage per transaction."""
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        help_text="Platform revenue % deducted from each successful payment (e.g. 10 = 10%)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Revenue Config"

    def __str__(self):
        return f"{self.percentage}% per transaction"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class OwnerWallet(models.Model):
    """Singleton — tracks accumulated platform revenue."""
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Owner Wallet"

    def __str__(self):
        return f"Owner Wallet — UGX {self.balance}"

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def credit(cls, amount):
        from django.db import transaction as db_tx
        with db_tx.atomic():
            wallet = cls.objects.select_for_update().get_or_create(pk=1)[0]
            wallet.balance += Decimal(str(amount))
            wallet.total_earned += Decimal(str(amount))
            wallet.save(update_fields=["balance", "total_earned", "updated_at"])


class WithdrawalRequest(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_PAID = "PAID"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
    ]

    PAYOUT_MTN = "MTN"
    PAYOUT_AIRTEL = "AIRTEL"
    PAYOUT_CHOICES = [
        (PAYOUT_MTN, "MTN Mobile Money"),
        (PAYOUT_AIRTEL, "Airtel Money"),
    ]

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payout_phone = models.CharField(max_length=20)
    payout_network = models.CharField(max_length=10, choices=PAYOUT_CHOICES, default=PAYOUT_MTN)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Withdrawal Request"
        ordering = ["-created_at"]

    def __str__(self):
        return f"UGX {self.amount} → {self.payout_phone} ({self.status})"
