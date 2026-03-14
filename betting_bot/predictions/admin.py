from django.contrib import admin
from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = (
        "home_team",
        "away_team",
        "prediction",
        "odds",
        "match_time",
        "match_date",
        "package",
        "is_active",
    )
    list_filter = ("package", "is_active", "match_date")
    search_fields = ("home_team", "away_team", "prediction")
    ordering = ("match_date", "match_time")
    list_editable = ("is_active",)
    date_hierarchy = "match_date"
