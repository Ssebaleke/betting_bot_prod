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
        # Get date
        if options['date']:
            target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            target_date = timezone.now().date()

        self.stdout.write(f"Sending predictions for {target_date}...")

        # Get today's predictions
        start_of_day = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end_of_day = timezone.make_aware(datetime.combine(target_date, datetime.max.time()))

        predictions = Prediction.objects.filter(
            is_active=True,
            publish_at__gte=start_of_day,
            publish_at__lte=end_of_day,
        ).select_related('fixture', 'market', 'package').order_by('package', 'fixture__start_time')

        if not predictions.exists():
            self.stdout.write(self.style.WARNING(f"No predictions found for {target_date}"))
            return

        # Group predictions by package
        predictions_by_package = {}
        for pred in predictions:
            package_name = pred.package.name
            if package_name not in predictions_by_package:
                predictions_by_package[package_name] = []
            predictions_by_package[package_name].append(pred)

        # Get active subscribers
        active_subscriptions = Subscription.objects.filter(
            is_active=True,
            end_date__gt=timezone.now()
        ).select_related('user', 'package')

        sent_count = 0
        failed_count = 0

        for subscription in active_subscriptions:
            try:
                # Get predictions for user's package
                package_predictions = predictions_by_package.get(subscription.package.name, [])
                
                if not package_predictions:
                    continue

                # Build message
                message = self._build_message(package_predictions, subscription.package.name, target_date)

                # Send to user
                telegram_profile = subscription.user.telegramprofile
                success = send_telegram_message(telegram_profile.telegram_id, message)

                if success:
                    sent_count += 1
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Sent to {subscription.user.username} ({subscription.package.name})"
                    ))
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                logger.error(f"Error sending to {subscription.user.username}: {e}")

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n📊 Summary:\n"
            f"✅ Sent: {sent_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📦 Packages: {len(predictions_by_package)}\n"
            f"🎯 Total predictions: {predictions.count()}"
        ))

    def _build_message(self, predictions, package_name, date):
        """Build formatted message with predictions"""
        message = (
            f"🔥 *DAILY PREDICTIONS* 🔥\n"
            f"📅 {date.strftime('%A, %B %d, %Y')}\n"
            f"📦 Package: {package_name}\n\n"
        )

        for i, pred in enumerate(predictions, 1):
            fixture = pred.fixture
            match_time = fixture.start_time.strftime('%H:%M') if fixture.start_time else 'TBD'
            
            message += (
                f"*{i}. {fixture.home_team} vs {fixture.away_team}*\n"
                f"⏰ {match_time}\n"
                f"🎯 Prediction: *{pred.selection}*\n"
                f"💰 Odds: *{pred.odds_value}*\n"
                f"📊 Market: {pred.market.name}\n\n"
            )

        message += (
            "━━━━━━━━━━━━━━━━━\n"
            "💡 *Bet Responsibly*\n"
            "Good luck! 🍀"
        )

        return message
