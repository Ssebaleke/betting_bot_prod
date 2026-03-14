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
        "send_date",
        "package",
        "is_active",
    )
    list_filter = ("package", "is_active", "send_date", "match_date")
    search_fields = ("home_team", "away_team", "prediction")
    ordering = ("send_date", "match_time")
    list_editable = ("is_active",)
    date_hierarchy = "send_date"
    fieldsets = (
        ("Match Details", {
            "fields": ("home_team", "away_team", "prediction", "odds", "match_time", "match_date")
        }),
        ("Scheduling", {
            "fields": ("send_date", "package", "is_active"),
            "description": "Set 'Send Date' to control when subscribers receive this prediction."
        }),
    )
