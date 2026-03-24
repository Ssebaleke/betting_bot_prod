"""
UGSMS v2 client - API key loaded from SMSConfig model (set via admin).
Docs: https://www.ugsms.com
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


def _get_config():
    from payments.models import SMSConfig
    config = SMSConfig.objects.filter(is_active=True).first()
    if not config:
        logger.error("No active SMSConfig found. Add one in Admin > SMS Config.")
        return None, None
    return config.api_key, config.sender_id


def send_sms(phone: str, message: str) -> bool:
    api_key, sender_id = _get_config()
    if not api_key:
        return False

    phone = _normalize_phone(phone)

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
        logger.error("UGSMS error: %s", data)
        return False
    except Exception as e:
        logger.error("UGSMS request failed for %s: %s", phone, e)
        return False
