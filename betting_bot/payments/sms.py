"""
UGSMS v2 client — API key read from UG_SMS_API_KEY env var.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

UGSMS_URL = "https://www.ugsms.com/api/v2/sms/send"


def _normalize_phone(phone: str) -> str:
    phone = phone.strip().lstrip("+")
    if phone.startswith("0"):
        phone = "256" + phone[1:]
    if not phone.startswith("256"):
        phone = "256" + phone
    return phone


def _get_api_key() -> str | None:
    key = getattr(settings, "UG_SMS_API_KEY", "").strip()
    if key:
        return key
    # fallback: check DB config
    from payments.models import SMSConfig
    config = SMSConfig.objects.filter(is_active=True).first()
    if config:
        return config.api_key
    logger.error("No UGSMS API key found. Set UG_SMS_API_KEY in .env")
    return None


def send_sms(phone: str, message: str) -> bool:
    api_key = _get_api_key()
    if not api_key:
        return False

    phone = _normalize_phone(phone)

    # Check and deduct balance
    from payments.models import SMSBalance
    balance = SMSBalance.get()
    if not balance.deduct():
        logger.error("SMS not sent to %s — zero credits remaining.", phone)
        return False

    try:
        resp = requests.post(
            UGSMS_URL,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"numbers": phone, "message_body": message},
            timeout=15,
        )
        data = resp.json()
        if data.get("success"):
            logger.info("SMS sent to %s", phone)
            return True
        # Refund credit if API rejected
        balance.credits += 1
        balance.save(update_fields=["credits", "updated_at"])
        logger.error("UGSMS error response: %s", data)
        return False
    except Exception as e:
        # Refund credit on network error
        balance.credits += 1
        balance.save(update_fields=["credits", "updated_at"])
        logger.error("UGSMS request failed for %s: %s", phone, e)
        return False
