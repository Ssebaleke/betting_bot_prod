from django.contrib import admin
from .models import (
    OddsProvider,
    Sport,
    League,
    Fixture,
    Market,
    Odd,
)


@admin.register(OddsProvider)
class OddsProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(Sport)
class SportAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "sport")
    list_filter = ("sport", "country")
    search_fields = ("name", "country")


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ("home_team", "away_team", "league", "start_time")
    list_filter = ("league",)
    search_fields = ("home_team", "away_team")
    ordering = ("start_time",)


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(Odd)
class OddAdmin(admin.ModelAdmin):
    list_display = (
        "fixture",
        "market",
        "selection",
        "value",
        "bookmaker",
        "source",
        "is_active",
    )
    list_filter = ("source", "market", "is_active", "bookmaker")
    search_fields = (
        "fixture__home_team",
        "fixture__away_team",
        "selection",
        "bookmaker",
    )
