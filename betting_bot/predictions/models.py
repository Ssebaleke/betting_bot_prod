from django.db import models
from django.utils import timezone
from packages.models import Package


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
        default=timezone.now,
        help_text="Date of the match"
    )
    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        help_text="Which package can see this prediction"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('match_date', 'match_time')

    def __str__(self):
        return f"{self.home_team} vs {self.away_team} | {self.prediction} | {self.match_date}"
