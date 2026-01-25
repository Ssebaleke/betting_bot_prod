import requests
from django.utils.dateparse import parse_datetime
from django.core.exceptions import ImproperlyConfigured

from odds.models import (
    OddsProvider,
    Sport,
    League,
    Fixture,
    Market,
    Odd,
)


API_URL = "https://api.the-odds-api.com/v4/sports/soccer/odds"


def get_active_provider():
    provider = OddsProvider.objects.filter(is_active=True).first()
    if not provider:
        raise ImproperlyConfigured(
            "No active OddsProvider found. Add one in Django admin."
        )
    return provider


def fetch_odds():
    provider = get_active_provider()

    params = {
        "apiKey": provider.api_key,
        "regions": "eu",
        "markets": "h2h",          # match winner
        "oddsFormat": "decimal",
    }

    response = requests.get(API_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    # Ensure base objects exist
    sport, _ = Sport.objects.get_or_create(
        slug="football",
        defaults={"name": "Football"},
    )

    market, _ = Market.objects.get_or_create(
        code="1X2",
        defaults={"name": "Match Winner"},
    )

    for match in data:
        league, _ = League.objects.get_or_create(
            sport=sport,
            name=match.get("sport_title", "Unknown League"),
            country="Unknown",
        )

        fixture, _ = Fixture.objects.update_or_create(
            external_id=match["id"],
            defaults={
                "league": league,
                "home_team": match["home_team"],
                "away_team": match["away_team"],
                "start_time": parse_datetime(match["commence_time"]),
            },
        )

        for bookmaker in match["bookmakers"]:
            for market_data in bookmaker["markets"]:
                for outcome in market_data["outcomes"]:

                    # DO NOT override manual odds
                    if Odd.objects.filter(
                        fixture=fixture,
                        market=market,
                        selection=outcome["name"],
                        source="manual",
                    ).exists():
                        continue

                    Odd.objects.update_or_create(
                        fixture=fixture,
                        market=market,
                        selection=outcome["name"],
                        bookmaker=bookmaker["title"],
                        source="api",
                        defaults={
                            "value": outcome["price"],
                            "is_active": True,
                        },
                    )
