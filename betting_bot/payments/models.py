from django.db import models
from django.contrib.auth.models import User
from packages.models import Package


class SMSConfig(models.Model):
    api_key = models.CharField(max_length=255, help_text="UGSMS v2 API Key")
    sender_id = models.CharField(max_length=20, default="BetTips", help_text="Sender name shown on SMS")
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
    PROVIDER_TYPE_CHOICES = (
        (PROVIDER_MAKYPAY, "MakyPay"),
        (PROVIDER_YOO, "Yo! Payments"),
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
