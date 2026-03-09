from __future__ import annotations

import uuid
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User

from packages.models import Package
from .models import Payment, PaymentProvider, PaymentProviderConfig
from .makypay import MakyPayClient, normalize_ug_phone

logger = logging.getLogger(__name__)


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
def initiate_payment(user: User, package: Package, phone: str) -> Payment:
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
        provider=provider,     # ✅ required by your model
        phone=phone_number,
        amount=amount,
        reference=reference,
        status=Payment.STATUS_PENDING,
    )

    client = MakyPayClient(
        base_url=provider.base_url,
        secret_key=config.secret_key,
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
    Subscription.objects.create(
        user=payment.user,
        package=payment.package,
    )
    logger.info("Subscription created for user=%s package=%s", payment.user.id, payment.package.name)

    return payment
