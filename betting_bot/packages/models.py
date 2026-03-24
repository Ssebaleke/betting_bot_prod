from django.db import models


class PackageCategory(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="e.g. Daily, Weekly, Monthly"
    )
    description = models.TextField(
        blank=True,
        help_text="Short description of this category"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Disable to hide this category"
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Display order (lower = first)"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        verbose_name = "Package Category"
        verbose_name_plural = "Package Categories"

    def __str__(self):
        return self.name


class Package(models.Model):
    category = models.ForeignKey(
        PackageCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="packages",
        help_text="Category this package belongs to (e.g. Daily, Weekly)"
    )

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="e.g. Ordinary, VIP, VVIP"
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
        category = self.category.name if self.category else "Uncategorized"
        return f"{category} - {self.name} ({self.duration_days} days)"
