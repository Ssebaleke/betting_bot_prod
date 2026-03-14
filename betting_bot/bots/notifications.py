"""
Telegram notification utilities
"""
import logging
import requests
from bots.models import TelegramBotConfig

logger = logging.getLogger(__name__)


def get_bot_token():
    """Get active Telegram bot token"""
    bot_config = TelegramBotConfig.objects.filter(is_active=True).first()
    if not bot_config:
        logger.error("No active Telegram bot configured")
        return None
    return bot_config.bot_token.strip()


def send_telegram_message(telegram_id: int, message: str, parse_mode: str = "Markdown"):
    """Send a message to a Telegram user using requests (no async)"""
    try:
        token = get_bot_token()
        if not token:
            return False
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={
            "chat_id": telegram_id,
            "text": message,
            "parse_mode": parse_mode
        }, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"Notification sent to telegram_id={telegram_id}")
            return True
        else:
            logger.error(f"Failed to send notification: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Failed to send notification to telegram_id={telegram_id}: {e}")
        return False


def notify_payment_success(user, package, payment):
    """Notify user of successful payment and subscription activation"""
    try:
        telegram_profile = user.telegramprofile
        message = (
            "✅ *Payment Successful!*\n\n"
            f"💰 Amount: UGX {payment.amount:,.0f}\n"
            f"📦 Package: {package.name}\n"
            f"⏰ Duration: {package.duration_days} days\n\n"
            "🎉 Your subscription is now active!\n"
            "Use /odds to get today's predictions."
        )
        send_telegram_message(telegram_profile.telegram_id, message)
    except Exception as e:
        logger.error(f"Failed to send success notification: {e}")


def notify_payment_failed(user, package, payment):
    """Notify user of failed payment"""
    try:
        telegram_profile = user.telegramprofile
        message = (
            "❌ *Payment Failed*\n\n"
            f"💰 Amount: UGX {payment.amount:,.0f}\n"
            f"📦 Package: {package.name}\n\n"
            "⚠️ Your payment could not be processed.\n\n"
            "*Possible reasons:*\n"
            "• Insufficient balance\n"
            "• Payment cancelled\n"
            "• Network timeout\n\n"
            "Please try again with /start"
        )
        send_telegram_message(telegram_profile.telegram_id, message)
    except Exception as e:
        logger.error(f"Failed to send failure notification: {e}")
