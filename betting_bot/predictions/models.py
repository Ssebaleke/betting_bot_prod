from django.db import models
from django.utils import timezone

from odds.models import Fixture, Market
from packages.models import Package


class Prediction(models.Model):
    SOURCE_CHOICES = (
        ("manual", "Manual"),
        ("logic", "Rule-based"),
        ("external", "External"),
    )

    fixture = models.ForeignKey(
        Fixture,
        on_delete=models.CASCADE,
        related_name="predictions",
    )

    market = models.ForeignKey(
        Market,
        on_delete=models.CASCADE,
    )

    selection = models.CharField(
        max_length=50,
        help_text="Chosen outcome (e.g. Chelsea, Over 2.5)",
    )

    odds_value = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Odds at the time of publishing",
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        help_text="Which package can see this prediction",
    )

    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="manual",
    )

    is_active = models.BooleanField(default=True)

    publish_at = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-publish_at",)

    def __str__(self):
        return f"{self.fixture} | {self.selection} ({self.package.name})"
