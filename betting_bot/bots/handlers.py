import requests
from django.conf import settings

from telegram import Update
from telegram.ext import ContextTypes

from bots.models import TelegramProfile


API_URL = "http://127.0.0.1:8000/api/predictions/today/"


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_user = update.effective_user

    # 1️⃣ Find Telegram profile
    try:
        profile = TelegramProfile.objects.select_related("user").get(
            telegram_id=telegram_user.id
        )
    except TelegramProfile.DoesNotExist:
        await update.message.reply_text(
            "❌ Your Telegram is not linked to an account.\n"
            "Please use /start to link your account."
        )
        return

    user = profile.user

    # 2️⃣ Call API using session authentication
    session = requests.Session()
    session.cookies = context.bot_data.get("django_cookies", {})

    response = session.get(API_URL)

    if response.status_code == 403:
        await update.message.reply_text(
            "❌ You do not have an active subscription."
        )
        return

    if response.status_code != 200:
        await update.message.reply_text(
            "⚠️ Unable to fetch today’s predictions. Try again later."
        )
        return

    data = response.json()

    if data["count"] == 0:
        await update.message.reply_text(
            "📭 No predictions available for today."
        )
        return

    # 3️⃣ Format message
    lines = []
    lines.append("🔥 *TODAY’S PICKS* 🔥\n")

    for idx, p in enumerate(data["predictions"], start=1):
        fixture = p["fixture"]
        lines.append(
            f"*{idx}. {fixture['home_team']} vs {fixture['away_team']}*\n"
            f"🧠 Pick: *{p['selection']}*\n"
            f"📊 Market: {p['market']}\n"
            f"💰 Odds: {p['odds']}\n"
        )

    message = "\n".join(lines)

    # 4️⃣ Send message
    await update.message.reply_text(
        message,
        parse_mode="Markdown"
    )
