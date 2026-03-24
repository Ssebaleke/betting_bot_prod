from __future__ import annotations

import uuid
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User

from packages.models import Package
from .models import Payment, PaymentProvider, PaymentProviderConfig, YooPaymentProvider
from .makypay import MakyPayClient, normalize_ug_phone
from .yoo_client import YooClient, make_reference, normalize_phone as normalize_yoo_phone

logger = logging.getLogger(__name__)


def get_or_create_phone_user(phone: str) -> User:
    """Get or create a Django user keyed by phone number."""
    from payments.makypay import normalize_ug_phone
    normalized = normalize_ug_phone(phone)
    username = f"web_{normalized}"
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={"first_name": normalized},
    )
    return user


def initiate_web_payment(phone: str, package_id: int) -> Payment:
    """Entry point for landing page payments - auto-creates user, forces SMS channel."""
    user = get_or_create_phone_user(phone)
    package = Package.objects.get(id=package_id, is_active=True)

    yoo = YooPaymentProvider.objects.filter(is_active=True).first()
    if yoo:
        return initiate_yoo_payment(user=user, package=package, phone=phone, delivery_channel="SMS")
    return initiate_payment(user=user, package=package, phone=phone, delivery_channel="SMS")


def get_active_provider() -> tuple[PaymentProvider, PaymentProviderConfig]:
    """
    Return active PaymentProvider + its active config.
    """
    provider = PaymentProvider.objects.filter(is_active=True).first()
    if not provider:
        raise ValueError("No active payment provider configured (PaymentProvider.is_active=True).")

    config = getattr(provider, "config", None)
    if not config or not config.is_active:
        raise ValueError("Active provider has no active config (PaymentProviderConfig.is_active=True).")

    return provider, config


@transaction.atomic
def initiate_payment(user: User, package: Package, phone: str, delivery_channel: str = "TELEGRAM") -> Payment:
    """
    1) Normalize phone
    2) Create Payment (PENDING)
    3) Call MakyPay request-to-pay
    4) Return Payment
    """
    phone_number = normalize_ug_phone(phone)

    # package price field
    price_val = getattr(package, "price", None)
    if price_val is None:
        # fallback if your package uses "amount"
        price_val = getattr(package, "amount", None)

    if price_val is None:
        raise ValueError("Package has no price/amount field. Add `price` or `amount` on Package.")

    amount = Decimal(str(price_val))

    # Prevent duplicate pending payments within 2 minutes (optional safety)
    recent_pending = Payment.objects.filter(
        user=user,
        status=Payment.STATUS_PENDING,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=2),
    ).order_by("-created_at").first()

    if recent_pending:
        logger.info("Returning recent pending payment ref=%s user=%s", recent_pending.reference, user.id)
        return recent_pending

    provider, config = get_active_provider()

    reference = str(uuid.uuid4())

    payment = Payment.objects.create(
        user=user,
        package=package,
        provider=provider,
        phone=phone_number,
        amount=amount,
        reference=reference,
        delivery_channel=delivery_channel,
        status=Payment.STATUS_PENDING,
    )

    client = MakyPayClient(
        base_url=provider.base_url,
        secret_key=config.secret_key,
        public_key=config.public_key,
    )

    # Use integer for UGX if no decimals
    amount_for_api = int(amount) if amount == amount.to_integral_value() else float(amount)

    logger.info("MakyPay START ref=%s phone=%s amount=%s", reference, phone_number, amount_for_api)

    # This is where previous code could hang and kill the worker
    client.request_to_pay(
        phone_number=phone_number,
        amount=amount_for_api,
        reference=reference,
        webhook_url=config.webhook_url,  # ✅ from admin config (must be PUBLIC url)
        currency="UGX",
    )

    logger.info("MakyPay END ref=%s", reference)

    return payment


@transaction.atomic
def initiate_yoo_payment(user: User, package: Package, phone: str, delivery_channel: str = "TELEGRAM") -> Payment:
    """
    Initiate a Yo! Payments USSD push collection.
    Credentials read from env vars first, fall back to YooPaymentProvider DB record.
    """
    from django.conf import settings

    api_username = getattr(settings, "YOO_API_USERNAME", "").strip()
    api_password = getattr(settings, "YOO_API_PASSWORD", "").strip()
    notification_url = getattr(settings, "YOO_NOTIFICATION_URL", "").strip()
    failure_url = getattr(settings, "YOO_FAILURE_URL", "").strip()

    if not api_username or not api_password:
        provider = YooPaymentProvider.objects.filter(is_active=True).first()
        if not provider:
            raise ValueError("No Yoo credentials found. Set YOO_API_USERNAME and YOO_API_PASSWORD in .env")
        api_username = provider.api_username
        api_password = provider.api_password
        notification_url = notification_url or provider.notification_url
        failure_url = failure_url or provider.failure_url

    if not notification_url or not failure_url:
        raise ValueError("Set YOO_NOTIFICATION_URL and YOO_FAILURE_URL in .env")

    price_val = getattr(package, "price", None) or getattr(package, "amount", None)
    if price_val is None:
        raise ValueError("Package has no price field.")

    amount = Decimal(str(price_val))
    phone_normalized = normalize_yoo_phone(phone)

    # Prevent duplicate pending within 2 minutes
    recent = Payment.objects.filter(
        user=user,
        status=Payment.STATUS_PENDING,
        provider_type=Payment.PROVIDER_YOO,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=2),
    ).order_by("-created_at").first()
    if recent:
        return recent

    reference = make_reference()  # UUID without hyphens

    payment = Payment.objects.create(
        user=user,
        package=package,
        provider=None,
        provider_type=Payment.PROVIDER_YOO,
        phone=phone_normalized,
        amount=amount,
        reference=reference,
        delivery_channel=delivery_channel,
        status=Payment.STATUS_PENDING,
    )

    client = YooClient(api_username=api_username, api_password=api_password)
    result = client.collect(
        phone=phone_normalized,
        amount=int(amount),
        reference=reference,
        notification_url=notification_url,
        failure_url=failure_url,
    )

    logger.info("Yoo collect result ref=%s result=%s", reference, result)

    if result.get("yoo_status") == "FAILED":
        payment.status = Payment.STATUS_FAILED
        payment.save(update_fields=["status"])
        raise ValueError(f"Yo! rejected payment: {result.get('error_message') or result.get('status_message')}")

    return payment


@transaction.atomic
def confirm_payment(reference: str, external_reference: str | None = None) -> Payment:
    """
    Webhook confirms payment and creates subscription.
    """
    from subscription.models import Subscription
    
    payment = Payment.objects.select_for_update().get(reference=reference)

    # idempotent
    if payment.status == Payment.STATUS_SUCCESS:
        return payment

    payment.status = Payment.STATUS_SUCCESS
    payment.external_reference = external_reference
    payment.save(update_fields=["status", "external_reference"])

    logger.info("Payment SUCCESS ref=%s ext_ref=%s", reference, external_reference)

    # Create subscription
    subscription = Subscription.objects.create(
        user=payment.user,
        package=payment.package,
    )
    logger.info("Subscription created for user=%s package=%s", payment.user.id, payment.package.name)

    # Send SMS confirmation for web payments
    if payment.delivery_channel == Payment.CHANNEL_SMS:
        try:
            from .sms import send_sms
            send_sms(
                payment.phone,
                f"Payment confirmed! UGX {int(payment.amount):,} for {payment.package.name} package. "
                f"Your predictions will be sent to this number daily. Bet Responsibly!"
            )
        except Exception as e:
            logger.error("SMS confirmation failed for ref=%s: %s", reference, e)

    # Send today's predictions if already sent for this package
    try:
        from predictions.models import Prediction

        today_predictions = list(Prediction.objects.filter(
            is_active=True,
            is_sent=True,
            send_date=timezone.localtime(timezone.now()).date(),
            package=payment.package,
        ).order_by('match_time'))

        if today_predictions:
            message = _build_predictions_message(
                today_predictions,
                payment.package.name,
                timezone.localtime(timezone.now()).date()
            )
            _deliver_predictions(payment.user, payment.phone, payment.delivery_channel, message)
            logger.info("Sent today's predictions to new subscriber user=%s channel=%s", payment.user.id, payment.delivery_channel)
    except Exception as e:
        logger.error("Failed to send predictions to new subscriber: %s", e)

    return payment


def _deliver_predictions(user, phone: str, channel: str, message: str):
    """Route prediction delivery to Telegram or SMS based on channel."""
    if channel == "SMS":
        from .sms import send_sms
        send_sms(phone, _strip_markdown(message))
    else:
        from bots.notifications import send_telegram_message
        try:
            telegram_profile = user.telegramprofile
            send_telegram_message(telegram_profile.telegram_id, message)
        except Exception as e:
            logger.error("Telegram delivery failed for user=%s: %s", user.id, e)


def _strip_markdown(text: str) -> str:
    """Remove Markdown formatting for plain SMS text."""
    import re
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'_+', '', text)
    return text


def _build_predictions_message(predictions, package_name, date):
    message = (
        f"🔥 *TODAY'S PREDICTIONS* 🔥\n"
        f"📅 {date.strftime('%A, %B %d, %Y')}\n"
        f"📦 Package: {package_name}\n\n"
    )
    total_odds = 1
    for i, pred in enumerate(predictions, 1):
        total_odds *= float(pred.odds)
        message += (
            f"*{i}. {pred.home_team} vs {pred.away_team}*\n"
            f"⏰ {pred.match_time.strftime('%H:%M')}\n"
            f"🎯 Prediction: *{pred.prediction}*\n"
            f"💰 Odds: *{pred.odds}*\n\n"
        )
    message += (
        f"━━━━━━━━━━━━━━━━━\n"
        f"🎰 *Total Combined Odds: {total_odds:.2f}*\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"💡 *Bet Responsibly*\n"
        f"Good luck! 🍀"
    )
    return message
