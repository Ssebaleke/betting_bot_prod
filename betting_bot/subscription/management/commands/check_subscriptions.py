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
from payments.models import Payment
from payments.sms import send_sms

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check subscriptions - deactivate expired and send notifications'

    def handle(self, *args, **options):
        now = timezone.now()
        
        self.deactivate_expired(now)
        self.send_expiry_reminders(now)

    def _notify(self, user, message):
        import re
        latest = Payment.objects.filter(
            user=user, status=Payment.STATUS_SUCCESS
        ).order_by("-created_at").first()

        if latest and latest.delivery_channel == Payment.CHANNEL_SMS:
            plain = re.sub(r'[^\x00-\x7F]+', '', message.replace("*", "").replace("_", ""))
            plain = re.sub(r'\n{3,}', '\n\n', plain).strip()
            send_sms(latest.phone, plain)
        else:
            try:
                send_telegram_message(user.telegramprofile.telegram_id, message)
            except Exception as e:
                logger.error("Telegram notify failed for user=%s: %s", user.id, e)

    def deactivate_expired(self, now):
        expired = Subscription.objects.filter(
            is_active=True,
            end_date__lte=now
        ).select_related('user', 'package')

        count = 0
        for subscription in expired:
            subscription.is_active = False
            subscription.save(update_fields=['is_active'])
            count += 1

            if subscription.expiry_notified:
                continue

            try:
                message = (
                    "⏰ *Subscription Expired*\n\n"
                    f"📦 Package: *{subscription.package.name}*\n"
                    f"📅 Expired: {subscription.end_date.strftime('%B %d, %Y')}\n\n"
                    "Renew to keep receiving predictions. Use /start to subscribe."
                )
                self._notify(subscription.user, message)
                subscription.expiry_notified = True
                subscription.save(update_fields=['expiry_notified'])
                self.stdout.write(self.style.WARNING(
                    f"⏰ Expired & notified: {subscription.user.username}"
                ))
            except Exception as e:
                logger.error(f"Failed to notify expired user {subscription.user.username}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Deactivated {count} expired subscriptions"))

    def send_expiry_reminders(self, now):
        """Send reminder to users whose subscription expires in 2 hours — only once."""
        reminder_window_start = now + timedelta(hours=2)
        reminder_window_end = now + timedelta(hours=3)

        expiring_soon = Subscription.objects.filter(
            is_active=True,
            reminder_sent=False,
            end_date__gte=reminder_window_start,
            end_date__lt=reminder_window_end,
        ).select_related('user', 'package')

        count = 0
        for subscription in expiring_soon:
            try:
                message = (
                    "Subscription Expiring Soon\n\n"
                    f"Package: {subscription.package.name}\n"
                    f"Expires: {subscription.end_date.strftime('%B %d, %Y %H:%M')}\n\n"
                    "Renew now to keep receiving daily predictions."
                )
                self._notify(subscription.user, message)
                subscription.reminder_sent = True
                subscription.save(update_fields=['reminder_sent'])
                count += 1
                self.stdout.write(self.style.WARNING(
                    f"⚠️ Reminder sent: {subscription.user.username} (expires tomorrow)"
                ))
            except Exception as e:
                logger.error(f"Failed to send reminder to {subscription.user.username}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Sent {count} expiry reminders"))
