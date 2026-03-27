"""
UGSMS v2 client — API key read from SMSConfig model set via Django admin.
"""
import logging
import requests

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
    from payments.models import SMSConfig
    config = SMSConfig.objects.filter(is_active=True).first()
    if not config:
        logger.error("No active SMSConfig found. Go to Admin > SMS Config and add your UGSMS API key.")
        return None
    return config.api_key


def send_sms(phone: str, message: str) -> bool:
    api_key = _get_api_key()
    if not api_key:
        return False

    phone = _normalize_phone(phone)

    from payments.models import SMSBalance, SMSLog
    balance = SMSBalance.get()
    if balance.credits <= 0:
        logger.error("SMS not sent to %s — zero credits remaining.", phone)
        return False

    try:
        from django.conf import settings
        sender_id = getattr(settings, "UG_SMS_SENDER_ID", "BetTips")
        resp = requests.post(
            UGSMS_URL,
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"numbers": phone, "message_body": message, "sender_id": sender_id},
            timeout=15,
        )
        data = resp.json()
        if data.get("success"):
            balance.deduct()
            SMSLog.objects.create(phone=phone, message=message, status=SMSLog.STATUS_SENT)
            logger.info("SMS sent to %s", phone)
            return True
        SMSLog.objects.create(phone=phone, message=message, status=SMSLog.STATUS_FAILED)
        logger.error("UGSMS error response: %s", data)
        return False
    except Exception as e:
        SMSLog.objects.create(phone=phone, message=message, status=SMSLog.STATUS_FAILED)
        logger.error("UGSMS request failed for %s: %s", phone, e)
        return False
