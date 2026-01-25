from django.db import models
from django.contrib.auth.models import User
from packages.models import Package


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


class Payment(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.PROTECT)
    provider = models.ForeignKey(PaymentProvider, on_delete=models.PROTECT)

    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    reference = models.CharField(max_length=100, unique=True)
    external_reference = models.CharField(
        max_length=100, blank=True, null=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reference} ({self.status})"
