"""
Management command to send daily predictions to active subscribers
Usage: python manage.py send_daily_predictions
"""
import re
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date as date_type
import logging

from predictions.models import Prediction
from subscription.models import Subscription
from bots.notifications import send_telegram_message
from payments.sms import send_sms
from payments.models import Payment

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
        local_now = timezone.localtime(now)  # Convert to Uganda time (EAT)
        target_date = (
            date_type.fromisoformat(options['date'])
            if options['date']
            else local_now.date()
        )
        current_time = local_now.time()  # Use local time for comparison

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

                # Determine delivery channel from latest successful payment
                latest_payment = Payment.objects.filter(
                    user=subscription.user,
                    status=Payment.STATUS_SUCCESS,
                ).order_by("-created_at").first()
                channel = latest_payment.delivery_channel if latest_payment else Payment.CHANNEL_TELEGRAM

                message = self._build_message(package_predictions, subscription.package.name, target_date)

                if channel == Payment.CHANNEL_SMS:
                    phone = latest_payment.phone
                    success = send_sms(phone, self._strip_markdown(message))
                else:
                    try:
                        telegram_profile = subscription.user.telegramprofile
                        success = send_telegram_message(telegram_profile.telegram_id, message)
                    except Exception as e:
                        logger.warning(
                            "Telegram delivery skipped for user=%s (no TelegramProfile or send failed): %s",
                            subscription.user.username, e
                        )
                        success = False

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

        total_predictions = predictions.count()

        # Only mark as sent if ALL subscribers were successfully notified
        if sent_count > 0 and failed_count == 0:
            predictions.update(is_sent=True)
            self.stdout.write(self.style.SUCCESS("All subscribers notified — predictions marked as sent."))
        elif sent_count > 0 and failed_count > 0:
            self.stdout.write(self.style.WARNING(
                f"{failed_count} subscriber(s) failed — predictions NOT marked as sent, will retry next run."
            ))
        else:
            self.stdout.write(self.style.ERROR("All sends failed — predictions NOT marked as sent, will retry next run."))
            return

        self.stdout.write(self.style.SUCCESS(
            f"\n📊 Summary:\n"
            f"✅ Sent: {sent_count}\n"
            f"❌ Failed: {failed_count}\n"
            f"📦 Packages: {len(predictions_by_package)}\n"
            f"🎯 Total predictions: {total_predictions}"
        ))

    def _strip_markdown(self, text: str) -> str:
        text = re.sub(r'\*+', '', text)
        text = re.sub(r'_+', '', text)
        return text

    def _build_message(self, predictions, package_name, date):
        total_odds = 1
        lines = [
            f"🔥 *DAILY PREDICTIONS* 🔥",
            f"📅 {date.strftime('%A, %B %d, %Y')}",
            f"📦 Package: {package_name}\n",
        ]
        for i, pred in enumerate(predictions, 1):
            total_odds *= float(pred.odds)
            lines.append(
                f"*{i}. {pred.home_team} vs {pred.away_team}*\n"
                f"⏰ {pred.match_time.strftime('%H:%M')}\n"
                f"🎯 Prediction: *{pred.prediction}*\n"
                f"💰 Odds: *{pred.odds}*"
            )
        lines.append(
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎰 *Total Combined Odds: {total_odds:.2f}*\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💡 *Bet Responsibly*\n"
            f"Good luck! 🍀"
        )
        return "\n".join(lines)
