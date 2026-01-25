from django.core.management.base import BaseCommand
from odds.services.fetch_odds import fetch_odds


class Command(BaseCommand):
    help = "Fetch odds from external provider"

    def handle(self, *args, **kwargs):
        fetch_odds()
        self.stdout.write(
            self.style.SUCCESS("Odds fetched successfully.")
        )
