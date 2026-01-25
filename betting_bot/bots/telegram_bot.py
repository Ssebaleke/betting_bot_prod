from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from asgiref.sync import sync_to_async
from django.utils import timezone
from django.contrib.auth.models import User

from bots.models import TelegramBotConfig, TelegramProfile
from packages.models import Package
from payments.services import initiate_payment
from subscription.models import Subscription


# =========================
# BOT TOKEN
# =========================

def get_active_bot_token():
    bot = TelegramBotConfig.objects.filter(is_active=True).first()
    if not bot:
        raise RuntimeError("No active Telegram bot configured")
    return bot.bot_token.strip()


# =========================
# DATABASE HELPERS
# =========================

@sync_to_async
def get_packages():
    return list(
        Package.objects.filter(is_active=True)
        .order_by("price")
        .values("id", "name", "price", "duration_days")
    )


@sync_to_async
def get_package(package_id):
    return Package.objects.get(id=package_id, is_active=True)


@sync_to_async
def ensure_telegram_profile(telegram_id, username):
    profile, _ = TelegramProfile.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={"username": username},
    )
    return profile


@sync_to_async
def has_active_subscription(telegram_id):
    return Subscription.objects.filter(
        user__telegramprofile__telegram_id=telegram_id,
        is_active=True,
        end_date__gt=timezone.now(),
    ).exists()


# =========================
# START / WELCOME
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    packages = await get_packages()

    keyboard = [
        [
            InlineKeyboardButton(
                text=f"{pkg['name']} – UGX {pkg['price']}",
                callback_data=f"PKG_{pkg['id']}",
            )
        ]
        for pkg in packages
    ]

    await update.message.reply_text(
        "👋 *Welcome to Vico BetBot*\n\n"
        "Get daily high-accuracy betting odds delivered straight to Telegram.\n\n"
        "👇 *Choose a package to continue:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# PACKAGE SELECTED
# =========================

async def package_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    package_id = int(query.data.replace("PKG_", ""))
    context.user_data["package_id"] = package_id

    await query.edit_message_text(
        text=(
            "📦 *Package selected*\n\n"
            "📞 Please enter your *MTN or Airtel* number to pay.\n"
            "Example: `0708826558`"
        ),
        parse_mode="Markdown",
    )


# =========================
# PHONE NUMBER HANDLER
# =========================

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "package_id" not in context.user_data:
        return

    phone = update.message.text.strip()
    if not phone.isdigit() or len(phone) < 9:
        await update.message.reply_text("❌ Invalid phone number.")
        return

    telegram_user = update.effective_user
    telegram_id = telegram_user.id

    await ensure_telegram_profile(telegram_id, telegram_user.username)

    package = await get_package(context.user_data["package_id"])

    # Initiate payment (USSD push)
    await sync_to_async(initiate_payment)(
        phone=phone,
        package=package,
        telegram_id=telegram_id,
    )

    await update.message.reply_text(
        "📲 *Payment request sent!*\n\n"
        "Please approve the payment on your phone.\n"
        "⏳ Waiting for confirmation...",
        parse_mode="Markdown",
    )

    context.user_data.clear()


# =========================
# ODDS (BLOCK IF NOT PAID)
# =========================

async def odds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    subscribed = await has_active_subscription(telegram_id)

    if not subscribed:
        await update.message.reply_text(
            "🚫 No active subscription.\n\n"
            "👇 Choose a package to continue:",
        )
        await start(update, context)
        return

    await update.message.reply_text(
        "🔥 *TODAY’S ODDS* 🔥\n\n"
        "⚽ Man City vs Arsenal\n"
        "➡️ Both teams to score @ 1.75\n\n"
        "⚽ Barcelona vs Sevilla\n"
        "➡️ Over 2.5 goals @ 1.68",
        parse_mode="Markdown",
    )


# =========================
# RUN BOT
# =========================

def run_bot():
    token = get_active_bot_token()

    app = (
        ApplicationBuilder()
        .token(token)
        .connect_timeout(30)
        .read_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("odds", odds))
    app.add_handler(CallbackQueryHandler(package_selected, pattern="^PKG_"))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
    )

    print("✅ Telegram bot is running and polling...")
    app.run_polling()
