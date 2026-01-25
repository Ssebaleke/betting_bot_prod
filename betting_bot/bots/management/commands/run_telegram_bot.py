from django.core.management.base import BaseCommand
from bots.telegram_bot import run_bot


class Command(BaseCommand):
    help = "Run Telegram bot"

    def handle(self, *args, **kwargs):
        run_bot()
