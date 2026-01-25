import uuid
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction

from .models import Payment, PaymentProviderConfig
from .makypay import MakyPayClient
from subscription.services import create_subscription


def get_active_makypay_config():
    config = PaymentProviderConfig.objects.filter(
        is_active=True,
        provider__is_active=True,
        provider__name__iexact="MakyPay"
    ).select_related("provider").first()

    if not config:
        raise ImproperlyConfigured("MakyPay is not configured or inactive")

    return config


def initiate_payment(user, package, phone):
    """
    Initiate a MakyPay request-to-pay
    """
    config = get_active_makypay_config()
    reference = str(uuid.uuid4())

    payment = Payment.objects.create(
        user=user,
        package=package,
        provider=config.provider,
        phone=phone,
        amount=package.price,
        reference=reference,
        status=Payment.STATUS_PENDING,
    )

    client = MakyPayClient(
        base_url=config.provider.base_url,
        public_key=config.public_key,
        secret_key=config.secret_key,
    )

    client.request_to_pay(
        phone=phone,
        amount=str(package.price),
        reference=reference,
        webhook_url=config.webhook_url,
    )

    return payment


@transaction.atomic
def confirm_payment(reference, external_reference=None):
    """
    Called by webhook when payment is completed
    """
    payment = Payment.objects.select_for_update().get(reference=reference)

    if payment.status == Payment.STATUS_SUCCESS:
        return payment

    payment.status = Payment.STATUS_SUCCESS
    payment.external_reference = external_reference
    payment.save(update_fields=["status", "external_reference"])

    create_subscription(payment.user, payment.package)

    return payment
