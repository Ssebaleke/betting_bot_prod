from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from django.contrib.auth.models import User
from packages.models import Package

from .models import Payment, PaymentProvider, PaymentProviderConfig
from .makypay import MakyPayClient, normalize_ug_phone


SUCCESS_STATUSES = {"completed", "success", "successful", "paid"}


def get_active_provider() -> tuple[PaymentProvider, PaymentProviderConfig]:
    """
    Return the active provider + its active config.
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
    Creates PENDING Payment and triggers MakyPay request-to-pay.
    """
    phone_number = normalize_ug_phone(phone)

    # Get package price (adjust if your field name differs)
    amount_val = getattr(package, "price", None) or getattr(package, "amount", None)
    if amount_val is None:
        raise ValueError("Package is missing a price/amount field.")

    amount = Decimal(str(amount_val))

    # Prevent duplicate pending payments in last 2 minutes
    recent = Payment.objects.filter(
        user=user,
        status=Payment.STATUS_PENDING,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=2),
    ).order_by("-created_at").first()
    if recent:
        return recent

    provider, config = get_active_provider()

    reference = str(uuid.uuid4())

    payment = Payment.objects.create(
        user=user,
        package=package,
        provider=provider,              # ✅ required by your model
        phone=phone_number,
        amount=amount,
        reference=reference,
        status=Payment.STATUS_PENDING,
    )

    client = MakyPayClient(
        base_url=provider.base_url,
        secret_key=config.secret_key,
    )

    # MakyPay expects number - int is safer for UGX
    amount_for_api = int(amount) if amount == amount.to_integral_value() else float(amount)

    client.request_to_pay(
        phone_number=phone_number,
        amount=amount_for_api,
        reference=reference,
        webhook_url=config.webhook_url,  # ✅ comes from admin config
        currency="UGX",
    )

    return payment


@transaction.atomic
def confirm_payment(reference: str, external_reference: str | None = None) -> Payment:
    """
    Marks payment SUCCESS and activates the user's package/subscription (you will connect this to BetBot access).
    Idempotent: if already SUCCESS, it won't duplicate.
    """
    payment = Payment.objects.select_for_update().get(reference=reference)

    if payment.status == Payment.STATUS_SUCCESS:
        return payment

    payment.status = Payment.STATUS_SUCCESS
    payment.external_reference = external_reference
    payment.save(update_fields=["status", "external_reference"])

    # ✅ Hook point: activate bet access
    # If you have a Subscription model, update/create it here.
    # If you use User profile fields, set them here.
    #
    # Example pseudo:
    # - set user.is_paid=True
    # - set expiry based on package duration
    #
    # I need your Package model (duration field) + how you store active users
    # to complete this part perfectly.

    return payment
