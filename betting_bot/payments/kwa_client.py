"""
payments/kwa_client.py
KwaPay Uganda mobile money client.
Base URL: https://pay.kwaug.net/api/v1
"""
import logging
import uuid
import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://pay.kwaug.net/api/v1"
_TIMEOUT = 20


def normalize_phone(phone: str) -> str:
    phone = str(phone).strip().replace(" ", "").replace("-", "")
    if phone.startswith("+"):
        phone = phone[1:]
    if phone.startswith("0"):
        phone = "256" + phone[1:]
    if not phone.startswith("256"):
        phone = "256" + phone
    return phone


def make_reference() -> str:
    return uuid.uuid4().hex


class KwaPayClient:

    def __init__(self, primary_api: str, secondary_api: str):
        self.primary_api = (primary_api or "").strip()
        self.secondary_api = (secondary_api or "").strip()
        if not self.primary_api or not self.secondary_api:
            raise ValueError("KwaPay primary_api and secondary_api are required.")

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{_BASE_URL}/{endpoint.lstrip('/')}/"
        payload["primary_api"] = self.primary_api
        payload["secondary_api"] = self.secondary_api
        try:
            resp = requests.post(url, json=payload, timeout=_TIMEOUT)
            logger.warning("KWAPAY %s ← HTTP %s | %.500s", endpoint, resp.status_code, resp.text)
            return resp.json()
        except requests.RequestException as e:
            return {"error": True, "message": str(e)}
        except ValueError:
            return {"error": True, "message": "Invalid JSON from KwaPay"}

    def collect(self, phone: str, amount: int, reference: str, callback_url: str) -> dict:
        logger.warning("KWAPAY COLLECT → phone=%s amount=%s ref=%s", phone, amount, reference)
        return self._post("deposit", {
            "phone_number": normalize_phone(phone),
            "amount": int(amount),
            "callback": callback_url,
        })

    def check_status(self, internal_reference: str) -> dict:
        return self._post("transaction/info", {"reference": internal_reference})

    def withdraw(self, phone: str, amount: int, callback_url: str) -> dict:
        logger.warning("KWAPAY WITHDRAW → phone=%s amount=%s", phone, amount)
        return self._post("withdraw", {
            "phone_number": normalize_phone(phone),
            "amount": int(amount),
            "callback": callback_url,
        })
