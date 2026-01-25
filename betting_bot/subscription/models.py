from datetime import timedelta

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from packages.models import Package


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.PROTECT
    )

    start_date = models.DateTimeField(
        default=timezone.now
    )

    end_date = models.DateTimeField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-end_date']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        # Auto-calculate end_date if not provided
        if not self.end_date:
            self.end_date = self.start_date + timedelta(
                days=self.package.duration_days
            )

        # Auto-deactivate if expired
        if self.end_date <= timezone.now():
            self.is_active = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} → {self.package.name}"

    def has_expired(self):
        return timezone.now() > self.end_date
