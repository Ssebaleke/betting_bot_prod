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

        self.stdout.write(self.style.SUCCESS(f"Deactivated {count} expired subscriptions"))

    def send_expiry_reminders(self, now):
        self.stdout.write("Expiry reminders disabled.")
        return
