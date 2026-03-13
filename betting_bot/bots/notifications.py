"""
Telegram notification utilities
"""
import logging
from telegram import Bot
from asgiref.sync import async_to_sync
from bots.models import TelegramBotConfig

logger = logging.getLogger(__name__)


def get_bot_instance():
    """Get active Telegram bot instance"""
    bot_config = TelegramBotConfig.objects.filter(is_active=True).first()
    if not bot_config:
        logger.error("No active Telegram bot configured")
        return None
    return Bot(token=bot_config.bot_token.strip())


@async_to_sync
async def send_telegram_message(telegram_id: int, message: str, parse_mode: str = "Markdown"):
    """Send a message to a Telegram user"""
    try:
        bot = get_bot_instance()
        if not bot:
            return False
        
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode=parse_mode
        )
        logger.info(f"Notification sent to telegram_id={telegram_id}")
        return True
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
