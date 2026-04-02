import uuid
import hmac
import hashlib
import time
import requests
import logging

logger = logging.getLogger(__name__)

COLLECT_URL = "https://livepay.me/api/v1/collect-money"
SEND_URL = "https://livepay.me/api/v1/send-money"


def normalize_phone(phone: str) -> str:
    phone = str(phone).strip().replace(" ", "").replace("-", "").lstrip("+")
    if phone.startswith("0"):
        phone = "256" + phone[1:]
    if not phone.startswith("256"):
        phone = "256" + phone
    return phone


def detect_network(phone: str) -> str:
    """Detect MTN or AIRTEL from Uganda phone number."""
    phone = normalize_phone(phone)
    number = phone[3:]  # strip 256
    mtn_prefixes = ("77", "78", "76", "31", "39")
    airtel_prefixes = ("70", "75", "74", "20")
    if number[:2] in mtn_prefixes:
        return "MTN"
    if number[:2] in airtel_prefixes:
        return "AIRTEL"
    return "MTN"  # default


def make_reference() -> str:
    return uuid.uuid4().hex


class LivePayClient:
    TIMEOUT = 30

    def __init__(self, secret_key: str, public_key: str, pin: str = ""):
        self.secret_key = secret_key
        self.public_key = public_key
        self.pin = pin

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.secret_key}",
        }

    def collect(self, phone: str, amount: int, reference: str) -> dict:
        phone = normalize_phone(phone)
        network = detect_network(phone)
        payload = {
            "apikey": self.public_key,
            "reference": reference,
            "phone_number": phone,
            "amount": amount,
            "currency": "UGX",
            "network": network,
        }
        try:
            resp = requests.post(COLLECT_URL, json=payload, headers=self._headers(), timeout=self.TIMEOUT)
            data = resp.json()
            logger.info("LivePay collect ref=%s status=%s", reference, data.get("status"))
            return data
        except Exception as e:
            logger.error("LivePay collect error ref=%s: %s", reference, e)
            raise

    def send(self, phone: str, amount: int, reference: str) -> dict:
        phone = normalize_phone(phone)
        network = detect_network(phone)
        payload = {
            "apikey": self.public_key,
            "reference": reference,
            "phone_number": phone,
            "amount": amount,
            "currency": "UGX",
            "network": network,
            "pin": self.pin,
        }
        try:
            resp = requests.post(SEND_URL, json=payload, headers=self._headers(), timeout=self.TIMEOUT)
            data = resp.json()
            logger.info("LivePay send ref=%s status=%s", reference, data.get("status"))
            return data
        except Exception as e:
            logger.error("LivePay send error ref=%s: %s", reference, e)
            raise


def verify_webhook_signature(secret_key: str, signature_header: str, payload: dict) -> bool:
    """Verify LivePay webhook signature."""
    try:
        import re
        match = re.match(r"t=([0-9]+),v=([a-f0-9]{64})", signature_header or "")
        if not match:
            return False
        timestamp = match.group(1)
        received_sig = match.group(2)

        # Reject requests older than 5 minutes
        if abs(time.time() - int(timestamp)) > 300:
            logger.warning("LivePay webhook timestamp too old")
            return False

        # Build signed string: timestamp + sorted key+value pairs
        signed_data = timestamp
        for key in sorted(payload.keys()):
            signed_data += str(key) + str(payload[key])

        expected = hmac.new(
            secret_key.encode(),
            signed_data.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, received_sig)
    except Exception as e:
        logger.error("LivePay signature verification error: %s", e)
        return False
