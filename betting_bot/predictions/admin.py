from django.contrib import admin
from django.contrib import messages
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
        "send_time",
        "package",
        "is_active",
        "is_sent",
    )
    list_filter = ("package", "is_active", "send_date", "match_date")
    search_fields = ("home_team", "away_team", "prediction")
    ordering = ("send_date", "send_time")
    list_editable = ("is_active",)
    readonly_fields = ("is_sent",)
    date_hierarchy = "send_date"
    actions = ["mark_unsent"]
    fieldsets = (
        ("Match Details", {
            "fields": ("home_team", "away_team", "prediction", "odds", "match_time", "match_date")
        }),
        ("Scheduling", {
            "fields": ("send_date", "send_time", "package", "is_active", "is_sent"),
            "description": "Set 'Send Date' and 'Send Time' to control when subscribers receive this prediction. is_sent is managed automatically."
        }),
    )

    def mark_unsent(self, request, queryset):
        updated = queryset.update(is_sent=False)
        self.message_user(request, f"{updated} prediction(s) marked as unsent — scheduler will resend them.", messages.SUCCESS)
    mark_unsent.short_description = "Mark selected as UNSENT (resend on next scheduler run)"
