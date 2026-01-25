from django.contrib import admin
from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "fixture",
        "selection",
        "odds_value",
        "package",
        "is_active",
        "publish_at",
    )

    list_filter = (
        "package",
        "is_active",
        "source",
        "market",
    )

    search_fields = (
        "fixture__home_team",
        "fixture__away_team",
        "selection",
    )

    ordering = ("-publish_at",)
