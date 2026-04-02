"""
Management command to send daily predictions to active subscribers
Usage: python manage.py send_daily_predictions
"""
import re
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date as date_type
import logging

from predictions.models import Prediction, PredictionDelivery
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
        # track per package: how many succeeded vs total attempted
        package_sent = {}    # pkg_name -> success count
        package_total = {}   # pkg_name -> total attempted

        for subscription in active_subscriptions:
            try:
                package_predictions = predictions_by_package.get(subscription.package.name, [])
                if not package_predictions:
                    continue

                pkg_name = subscription.package.name

                # Skip if already delivered to this user today for this package
                try:
                    already_delivered = PredictionDelivery.objects.filter(
                        user=subscription.user,
                        send_date=target_date,
                        package=subscription.package,
                    ).exists()
                    if already_delivered:
                        self.stdout.write(f"  Skipping {subscription.user.username} — already delivered today")
                        continue
                except Exception:
                    pass  # table may not exist yet, continue sending

                package_total[pkg_name] = package_total.get(pkg_name, 0) + 1

                # Determine delivery channel from latest successful payment
                latest_payment = Payment.objects.filter(
                    user=subscription.user,
                    status=Payment.STATUS_SUCCESS,
                ).order_by("-created_at").first()
                channel = latest_payment.delivery_channel if latest_payment else Payment.CHANNEL_TELEGRAM

                message = self._build_message(package_predictions, pkg_name, target_date)

                if channel == Payment.CHANNEL_SMS:
                    phone = latest_payment.phone
                    success = send_sms(phone, self._build_sms_message(package_predictions, pkg_name, target_date))
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
                    package_sent[pkg_name] = package_sent.get(pkg_name, 0) + 1
                    try:
                        PredictionDelivery.objects.get_or_create(
                            user=subscription.user,
                            send_date=target_date,
                            package=subscription.package,
                        )
                    except Exception as e:
                        logger.warning("PredictionDelivery record failed for %s: %s", subscription.user.username, e)
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Sent to {subscription.user.username} ({pkg_name})"
                    ))
                else:
                    failed_count += 1
                    self.stdout.write(self.style.ERROR(
                        f"✗ Failed: {subscription.user.username} ({pkg_name})"
                    ))

            except Exception as e:
                failed_count += 1
                logger.error(f"Error sending to {subscription.user.username}: {e}")

        total_predictions = predictions.count()

        # Only mark is_sent=True for packages where ALL subscribers were notified
        fully_sent_packages = [
            pkg for pkg in package_total
            if package_sent.get(pkg, 0) == package_total[pkg]
        ]
        partial_packages = [
            pkg for pkg in package_total
            if package_sent.get(pkg, 0) < package_total[pkg]
        ]

        if fully_sent_packages:
            predictions.filter(package__name__in=fully_sent_packages).update(is_sent=True)
            self.stdout.write(self.style.SUCCESS(
                f"Marked is_sent=True for packages (all delivered): {', '.join(fully_sent_packages)}"
            ))
        if partial_packages:
            self.stdout.write(self.style.WARNING(
                f"NOT marking is_sent for packages with failed deliveries: {', '.join(partial_packages)} — scheduler will retry."
            ))
        if failed_count > 0:
            self.stdout.write(self.style.WARNING(f"{failed_count} subscriber(s) failed delivery — will retry on next run."))

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
        text = re.sub(r'[^\x00-\x7F]+', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _build_sms_message(self, predictions, package_name, date):
        """Build compact SMS — one message per prediction to stay under 160 chars."""
        total_odds = 1
        for pred in predictions:
            total_odds *= float(pred.odds)
        # Single compact message
        lines = [f"TIPS {date.strftime('%d/%m/%Y')}:"]
        for i, pred in enumerate(predictions, 1):
            lines.append(f"{i}.{pred.home_team} v {pred.away_team} | {pred.prediction} @{pred.odds} ({pred.match_time.strftime('%H:%M')})")
        lines.append(f"Odds:{total_odds:.2f} Bet Responsibly")
        return "\n".join(lines)

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
