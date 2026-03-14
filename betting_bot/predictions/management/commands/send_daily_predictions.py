"""
Management command to send daily predictions to active subscribers
Usage: python manage.py send_daily_predictions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
import logging

from predictions.models import Prediction
from subscription.models import Subscription
from bots.notifications import send_telegram_message

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send daily predictions to active subscribers via Telegram'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to send predictions for (YYYY-MM-DD). Default: today',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        target_date = (
            datetime.strptime(options['date'], '%Y-%m-%d').date()
            if options['date']
            else now.date()
        )
        current_time = now.time()

        self.stdout.write(f"Sending predictions for {target_date} at {current_time.strftime('%H:%M')}...")

        # Only get predictions that haven't been sent yet
        predictions = Prediction.objects.filter(
            is_active=True,
            is_sent=False,
            send_date=target_date,
            send_time__lte=current_time,
        ).select_related('package').order_by('package', 'match_time')

        if not predictions.exists():
            self.stdout.write(self.style.WARNING(f"No unsent predictions found for {target_date}"))
            return

        # Group predictions by package
        predictions_by_package = {}
        for pred in predictions:
            pkg = pred.package.name
            if pkg not in predictions_by_package:
                predictions_by_package[pkg] = []
            predictions_by_package[pkg].append(pred)

        # Get active subscribers
        active_subscriptions = Subscription.objects.filter(
            is_active=True,
            end_date__gt=timezone.now()
        ).select_related('user', 'package')

        sent_count = 0
        failed_count = 0
        notified_users = set()

        for subscription in active_subscriptions:
            try:
                if subscription.user.id in notified_users:
                    continue

                package_predictions = predictions_by_package.get(subscription.package.name, [])
                if not package_predictions:
                    continue

                message = self._build_message(package_predictions, subscription.package.name, target_date)
                telegram_profile = subscription.user.telegramprofile
                success = send_telegram_message(telegram_profile.telegram_id, message)

                if success:
                    sent_count += 1
                    notified_users.add(subscription.user.id)
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Sent to {subscription.user.username} ({subscription.package.name})"
                    ))
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                logger.error(f"Error sending to {subscription.user.username}: {e}")

        # Mark predictions as sent so they don't get sent again
        predictions.update(is_sent=True)

        self.stdout.write(self.style.SUCCESS(
            f"\n📊 Summary:\n"
            f"✅ Sent: {sent_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📦 Packages: {len(predictions_by_package)}\n"
            f"🎯 Total predictions: {predictions.count()}"
        ))

    def _build_message(self, predictions, package_name, date):
        message = (
            f"🔥 *DAILY PREDICTIONS* 🔥\n"
            f"📅 {date.strftime('%A, %B %d, %Y')}\n"
            f"📦 Package: {package_name}\n\n"
        )

        total_odds = 1
        for i, pred in enumerate(predictions, 1):
            total_odds *= float(pred.odds)
            message += (
                f"*{i}. {pred.home_team} vs {pred.away_team}*\n"
                f"⏰ {pred.match_time.strftime('%H:%M')}\n"
                f"🎯 Prediction: *{pred.prediction}*\n"
                f"💰 Odds: *{pred.odds}*\n\n"
            )

        message += (
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎰 *Total Combined Odds: {total_odds:.2f}*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💡 *Bet Responsibly*\n"
            f"Good luck! 🍀"
        )

        return message
