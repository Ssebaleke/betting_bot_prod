from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
from bots.handlers import today_command
from packages.models import Package
from payments.models import YooPaymentProvider
from payments.services import initiate_payment, initiate_yoo_payment
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
    try:
        profile = TelegramProfile.objects.get(telegram_id=telegram_id)
        if not profile.user:
            user = User.objects.create_user(
                username=f"tg_{telegram_id}",
                first_name=username or "User",
            )
            profile.user = user
            profile.save()
    except TelegramProfile.DoesNotExist:
        user = User.objects.create_user(
            username=f"tg_{telegram_id}",
            first_name=username or "User",
        )
        profile = TelegramProfile.objects.create(
            telegram_id=telegram_id,
            username=username,
            user=user,
        )
    return profile


@sync_to_async
def get_active_subscription(telegram_id):
    return Subscription.objects.filter(
        user__telegramprofile__telegram_id=telegram_id,
        is_active=True,
        end_date__gt=timezone.now(),
    ).select_related("package").first()


@sync_to_async
def do_initiate_payment(user, package, phone):
    if YooPaymentProvider.objects.filter(is_active=True).exists():
        return initiate_yoo_payment(user=user, package=package, phone=phone)
    return initiate_payment(user=user, package=package, phone=phone)


# =========================
# /start
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    packages = await get_packages()
    keyboard = [
        [InlineKeyboardButton(
            text=f"{pkg['name']} – UGX {pkg['price']} / {pkg['duration_days']} days",
            callback_data=f"PKG_{pkg['id']}",
        )]
        for pkg in packages
    ]
    await update.message.reply_text(
        "👋 *Welcome to Vico BetBot*\n\n"
        "Get daily high-accuracy betting predictions delivered straight to Telegram.\n\n"
        "👇 *Choose a package to subscribe:*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# =========================
# /help
# =========================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Available Commands*\n\n"
        "/start — Subscribe or renew your package\n"
        "/today — Get today's predictions\n"
        "/mysubscription — Check your subscription status\n"
        "/renew — Renew your current package\n"
        "/help — Show this help message\n\n"
        "💬 For support, contact the admin.",
        parse_mode="Markdown",
    )


# =========================
# /mysubscription
# =========================

async def my_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    subscription = await get_active_subscription(telegram_id)

    if not subscription:
        await update.message.reply_text(
            "❌ You have no active subscription.\n\nUse /start to subscribe.",
        )
        return

    now = timezone.now()
    days_remaining = (subscription.end_date - now).days
    expiry_str = timezone.localtime(subscription.end_date).strftime("%B %d, %Y at %H:%M")

    await update.message.reply_text(
        f"📦 *Your Subscription*\n\n"
        f"✅ Package: *{subscription.package.name}*\n"
        f"📅 Expires: {expiry_str}\n"
        f"⏳ Days remaining: *{days_remaining} day(s)*\n\n"
        f"Use /today to get today's predictions.",
        parse_mode="Markdown",
    )


# =========================
# /renew
# =========================

async def renew(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    subscription = await get_active_subscription(telegram_id)

    if subscription:
        context.user_data["package_id"] = subscription.package.id
        await update.message.reply_text(
            f"🔄 *Renew {subscription.package.name}*\n\n"
            f"📞 Enter your MTN or Airtel number to pay:\n"
            f"Example: `0708826558`",
            parse_mode="Markdown",
        )
    else:
        await start(update, context)


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
            "📦 *Package selected!*\n\n"
            "📞 Enter your *MTN or Airtel* number to pay:\n"
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
        await update.message.reply_text("❌ Invalid phone number. Please enter a valid MTN or Airtel number.")
        return

    telegram_user = update.effective_user
    profile = await ensure_telegram_profile(telegram_user.id, telegram_user.username)
    package = await get_package(context.user_data["package_id"])

    await update.message.reply_text(
        "⏳ *Processing your payment...*\n\nPlease wait.",
        parse_mode="Markdown",
    )

    try:
        await do_initiate_payment(user=profile.user, package=package, phone=phone)
        await update.message.reply_text(
            "📲 *Payment request sent!*\n\n"
            "✅ Please *approve the payment* on your phone.\n\n"
            "⏳ You will receive a confirmation message once payment is complete.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ *Payment failed:* {str(e)}\n\nPlease try again with /start",
            parse_mode="Markdown",
        )

    context.user_data.clear()


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
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("mysubscription", my_subscription))
    app.add_handler(CommandHandler("renew", renew))
    app.add_handler(CallbackQueryHandler(package_selected, pattern="^PKG_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone))

    print("✅ Telegram bot is running and polling...")
    app.run_polling()
