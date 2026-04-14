import uuid
import hmac
import hashlib
import time
import requests
import logging

logger = logging.getLogger(__name__)

COLLECT_URL = "https://livepay.me/api/collect-money"
SEND_URL = "https://livepay.me/api/send-money"


def normalize_phone(phone: str) -> str:
    phone = str(phone).strip().replace(" ", "").replace("-", "").lstrip("+")
    if phone.startswith("0"):
        phone = "256" + phone[1:]
    if not phone.startswith("256"):
        phone = "256" + phone
    return phone


def detect_network(phone: str) -> str:
    phone = normalize_phone(phone)
    number = phone[3:]
    mtn_prefixes = ("77", "78", "76", "31", "39")
    airtel_prefixes = ("70", "75", "74", "20")
    if number[:2] in mtn_prefixes:
        return "MTN"
    if number[:2] in airtel_prefixes:
        return "AIRTEL"
    return "MTN"


def make_reference() -> str:
    return uuid.uuid4().hex[:30]


class LivePayClient:
    TIMEOUT = 30

    def __init__(self, secret_key: str, public_key: str, pin: str = ""):
        self.account_number = public_key   # public_key stores accountNumber
        self.api_key = secret_key          # secret_key stores Bearer token
        self.pin = pin

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def collect(self, phone: str, amount: int, reference: str) -> dict:
        phone = normalize_phone(phone)
        ref = reference[:30]
        payload = {
            "accountNumber": self.account_number,
            "phoneNumber": phone,
            "amount": amount,
            "currency": "UGX",
            "reference": ref,
            "description": "Subscription payment",
        }
        try:
            resp = requests.post(COLLECT_URL, json=payload, headers=self._headers(), timeout=self.TIMEOUT)
            data = resp.json()
            logger.info("LivePay collect ref=%s response=%s", ref, data)
            return data
        except Exception as e:
            logger.error("LivePay collect error ref=%s: %s", ref, e)
            raise

    def send(self, phone: str, amount: int, reference: str, description: str = "Payout") -> dict:
        phone = normalize_phone(phone)
        ref = reference[:30]
        payload = {
            "accountNumber": self.account_number,
            "phoneNumber": phone,
            "amount": amount,
            "currency": "UGX",
            "reference": ref,
            "description": description,
        }
        try:
            resp = requests.post(SEND_URL, json=payload, headers=self._headers(), timeout=self.TIMEOUT)
            data = resp.json()
            logger.info("LivePay send ref=%s response=%s", ref, data)
            return data
        except Exception as e:
            logger.error("LivePay send error ref=%s: %s", ref, e)
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
