"""
Management command to handle subscription expiry
- Deactivates expired subscriptions
- Sends 1-day reminder before expiry
- Sends expiry notification when subscription expires
Usage: python manage.py check_subscriptions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from subscription.models import Subscription
from bots.notifications import send_telegram_message

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check subscriptions - deactivate expired and send notifications'

    def handle(self, *args, **options):
        now = timezone.now()
        
        self.deactivate_expired(now)
        self.send_expiry_reminders(now)

    def deactivate_expired(self, now):
        """Deactivate expired subscriptions and notify users"""
        expired = Subscription.objects.filter(
            is_active=True,
            end_date__lte=now
        ).select_related('user', 'package')

        count = 0
        for subscription in expired:
            subscription.is_active = False
            subscription.save(update_fields=['is_active'])
            count += 1

            # Notify user
            try:
                telegram_profile = subscription.user.telegramprofile
                message = (
                    "⏰ *Subscription Expired*\n\n"
                    f"📦 Package: {subscription.package.name}\n"
                    f"📅 Expired: {subscription.end_date.strftime('%B %d, %Y')}\n\n"
                    "You no longer have access to daily predictions.\n\n"
                    "🔄 *Renew your subscription to continue receiving predictions!*\n"
                    "Use /start to subscribe again."
                )
                send_telegram_message(telegram_profile.telegram_id, message)
                self.stdout.write(self.style.WARNING(
                    f"⏰ Expired & notified: {subscription.user.username}"
                ))
            except Exception as e:
                logger.error(f"Failed to notify expired user {subscription.user.username}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Deactivated {count} expired subscriptions"))

    def send_expiry_reminders(self, now):
        """Send reminder to users whose subscription expires in 1 day"""
        reminder_time = now + timedelta(days=1)

        expiring_soon = Subscription.objects.filter(
            is_active=True,
            end_date__date=reminder_time.date()
        ).select_related('user', 'package')

        count = 0
        for subscription in expiring_soon:
            try:
                telegram_profile = subscription.user.telegramprofile
                message = (
                    "⚠️ *Subscription Expiring Soon!*\n\n"
                    f"📦 Package: {subscription.package.name}\n"
                    f"📅 Expires: {subscription.end_date.strftime('%B %d, %Y at %H:%M')}\n\n"
                    "Your subscription expires *tomorrow*!\n\n"
                    "🔄 *Renew now to keep receiving daily predictions.*\n"
                    "Use /start to renew."
                )
                send_telegram_message(telegram_profile.telegram_id, message)
                count += 1
                self.stdout.write(self.style.WARNING(
                    f"⚠️ Reminder sent: {subscription.user.username} (expires tomorrow)"
                ))
            except Exception as e:
                logger.error(f"Failed to send reminder to {subscription.user.username}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Sent {count} expiry reminders"))
