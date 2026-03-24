from telegram import Update
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async
from django.utils import timezone

from bots.models import TelegramProfile
from subscription.models import Subscription
from predictions.models import Prediction


@sync_to_async
def get_today_predictions(telegram_id):
    try:
        profile = TelegramProfile.objects.select_related("user").get(telegram_id=telegram_id)
    except TelegramProfile.DoesNotExist:
        return None, None

    subscription = Subscription.objects.filter(
        user=profile.user,
        is_active=True,
        end_date__gt=timezone.now()
    ).select_related("package").first()

    if not subscription:
        return profile, None

    local_now = timezone.localtime(timezone.now())
    predictions = list(
        Prediction.objects.filter(
            is_active=True,
            is_sent=True,
            send_date=local_now.date(),
            package=subscription.package,
        ).order_by("match_time")
    )
    return profile, predictions


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    profile, predictions = await get_today_predictions(telegram_id)

    if profile is None:
        await update.message.reply_text(
            "❌ Your Telegram is not linked to an account.\nUse /start to get started."
        )
        return

    if predictions is None:
        await update.message.reply_text(
            "🚫 No active subscription.\nUse /start to subscribe."
        )
        return

    if not predictions:
        await update.message.reply_text("📭 No predictions sent yet for today. Check back later.")
        return

    subscription = await sync_to_async(
        lambda: Subscription.objects.filter(
            user__telegramprofile__telegram_id=telegram_id,
            is_active=True
        ).select_related("package").first()
    )()

    total_odds = 1
    lines = [
        f"🔥 *TODAY'S PREDICTIONS* 🔥\n"
        f"📅 {timezone.localtime(timezone.now()).strftime('%A, %B %d, %Y')}\n"
        f"📦 Package: {subscription.package.name}\n"
    ]
    for i, pred in enumerate(predictions, 1):
        total_odds *= float(pred.odds)
        lines.append(
            f"*{i}. {pred.home_team} vs {pred.away_team}*\n"
            f"⏰ {pred.match_time.strftime('%H:%M')}\n"
            f"🎯 Prediction: *{pred.prediction}*\n"
            f"💰 Odds: *{pred.odds}*\n"
        )
    lines.append(
        f"━━━━━━━━━━━━━━━━━\n"
        f"🎰 *Total Combined Odds: {total_odds:.2f}*\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💡 *Bet Responsibly* 🍀"
    )

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
