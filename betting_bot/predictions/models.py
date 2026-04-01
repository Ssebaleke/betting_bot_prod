from django.db import models
from django.utils import timezone
from packages.models import Package
from django.contrib.auth.models import User


class Prediction(models.Model):

    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    prediction = models.CharField(
        max_length=100,
        help_text="e.g. Arsenal to win, Over 2.5, BTTS Yes"
    )
    odds = models.DecimalField(
        max_digits=6,
        decimal_places=2,
    )
    match_time = models.TimeField(
        help_text="Match kick-off time"
    )
    match_date = models.DateField(
        help_text="Date match is played"
    )
    send_date = models.DateField(
        default=timezone.now,
        help_text="Date to send this prediction to subscribers (can be before match day)"
    )
    send_time = models.TimeField(
        default="08:00",
        help_text="Time to send this prediction to subscribers"
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        help_text="Which package receives this prediction"
    )
    is_active = models.BooleanField(default=True)
    is_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('send_date', 'match_time')

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} | {self.prediction} | Send: {self.send_date}"


class PredictionDelivery(models.Model):
    """Tracks per-user delivery so we never double-send or miss anyone."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    send_date = models.DateField()
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    delivered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'send_date', 'package')

    def __str__(self):
        return f"{self.user.username} | {self.package.name} | {self.send_date}"
