from django.core.management.base import BaseCommand
from django.utils import timezone
from subscription.models import Subscription


class Command(BaseCommand):
    help = "Deactivate expired subscriptions"

    def handle(self, *args, **options):
        expired = Subscription.objects.filter(
            is_active=True,
            end_date__lte=timezone.now()
        )

        count = expired.update(is_active=False)

        self.stdout.write(
            self.style.SUCCESS(f"{count} subscriptions deactivated")
        )
