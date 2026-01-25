from django.db import models


class Package(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="e.g. Ordinary, VIP, VVIP, hub"
    )

    description = models.TextField(
        blank=True,
        help_text="What this package offers"
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Package price"
    )

    duration_days = models.PositiveIntegerField(
        help_text="How long the package lasts (in days)"
    )

    level = models.PositiveIntegerField(
        default=1,
        help_text="Access rank. Higher number = higher access"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Disable to stop new subscriptions"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["level"]

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"
