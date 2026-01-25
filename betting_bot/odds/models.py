from django.db import models


class OddsProvider(models.Model):
    name = models.CharField(max_length=50)
    api_key = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "active" if self.is_active else "inactive"
        return f"{self.name} ({status})"


class Sport(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class League(models.Model):
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.country})"


class Fixture(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE)
    home_team = models.CharField(max_length=100)
    away_team = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    external_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.home_team} vs {self.away_team}"


class Market(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


class Odd(models.Model):
    SOURCE_CHOICES = (
        ("api", "API"),
        ("manual", "Manual"),
    )

    fixture = models.ForeignKey(Fixture, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    selection = models.CharField(max_length=50)   # Home / Draw / Away
    value = models.DecimalField(max_digits=6, decimal_places=2)
    bookmaker = models.CharField(max_length=50, blank=True)
    source = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default="api",
    )
    is_active = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            "fixture",
            "market",
            "selection",
            "bookmaker",
            "source",
        )

    def __str__(self):
        return f"{self.fixture} | {self.market} | {self.selection} @ {self.value}"
