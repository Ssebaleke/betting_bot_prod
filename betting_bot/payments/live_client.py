"""
payments/live_client.py
=======================
Client for the LivePay API (Uganda).
Endpoints:
  POST https://livepay.me/api/v1/collect-money  — initiate collection
  POST https://livepay.me/api/v1/send-money      — send money (disbursement)
  POST https://livepay.me/api/v1/transaction-status.php — check status
"""

import hashlib
import hmac
import logging
import time
import uuid

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://livepay.me/api/v1"
_TIMEOUT = 15


class LivePayClient:

    def __init__(self, public_key: str, secret_key: str):
        self.public_key = (public_key or "").strip()
        self.secret_key = (secret_key or "").strip()
        if not self.public_key or not self.secret_key:
            raise ValueError("LivePay public_key and secret_key must be set.")

    def collect(self, amount: int, phone: str, network: str, reference: str = None) -> dict:
        ref = reference or str(uuid.uuid4()).replace("-", "")
        payload = {
            "apikey": self.public_key,
            "reference": ref,
            "phone_number": self._normalize_phone(phone),
            "amount": int(amount),
            "currency": "UGX",
            "network": network.upper(),
        }
        try:
            logger.warning("LIVEPAY COLLECT → phone=%s amount=%s network=%s ref=%s",
                           payload["phone_number"], payload["amount"], payload["network"], ref)
            resp = requests.post(
                f"{_BASE_URL}/collect-money",
                json=payload,
                headers={"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/json"},
                timeout=_TIMEOUT,
            )
            logger.warning("LIVEPAY COLLECT ← HTTP %s | %.600s", resp.status_code, resp.text)
            return resp.json()
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc)}
        except ValueError:
            return {"status": "error", "message": "Invalid JSON from LivePay"}

    def send(self, amount: int, phone: str, network: str, pin: str, reference: str = None) -> dict:
        ref = reference or str(uuid.uuid4()).replace("-", "")
        payload = {
            "apikey": self.public_key,
            "reference": ref,
            "phone_number": self._normalize_phone(phone),
            "amount": int(amount),
            "currency": "UGX",
            "network": network.upper(),
            "pin": pin,
        }
        try:
            logger.warning("LIVEPAY SEND → phone=%s amount=%s ref=%s", payload["phone_number"], payload["amount"], ref)
            resp = requests.post(
                f"{_BASE_URL}/send-money",
                json=payload,
                headers={"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/json"},
                timeout=_TIMEOUT,
            )
            logger.warning("LIVEPAY SEND ← HTTP %s | %.600s", resp.status_code, resp.text)
            return resp.json()
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc)}
        except ValueError:
            return {"status": "error", "message": "Invalid JSON from LivePay"}

    def check_status(self, transaction_id: str) -> dict:
        payload = {"apikey": self.public_key, "transaction_id": transaction_id}
        try:
            resp = requests.post(
                f"{_BASE_URL}/transaction-status.php",
                json=payload,
                headers={"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/json"},
                timeout=_TIMEOUT,
            )
            logger.warning("LIVEPAY STATUS ← HTTP %s | %.600s", resp.status_code, resp.text)
            return resp.json()
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc)}
        except ValueError:
            return {"status": "error", "message": "Invalid JSON from LivePay"}

    @staticmethod
    def get_transaction_status(data: dict) -> str:
        return str(data.get("transaction", {}).get("status", "")).upper()

    @staticmethod
    def detect_network(phone: str) -> str:
        phone = str(phone).strip().replace(" ", "").replace("-", "")
        if phone.startswith("+"): phone = phone[1:]
        if phone.startswith("0"): phone = "256" + phone[1:]
        if not phone.startswith("256"): phone = "256" + phone
        local = phone[3:]
        for p in ("77", "78", "76", "39", "31"):
            if local.startswith(p): return "MTN"
        for p in ("70", "74", "75", "20", "72", "73"):
            if local.startswith(p): return "AIRTEL"
        return "MTN"

    @staticmethod
    def verify_webhook_signature(secret_key: str, signature_header: str, payload: dict) -> bool:
        try:
            parts = {}
            for part in signature_header.split(","):
                k, v = part.split("=", 1)
                parts[k.strip()] = v.strip()
            timestamp = parts.get("t", "")
            received_sig = parts.get("v", "")
            if not timestamp or not received_sig:
                return False
            if abs(time.time() - int(timestamp)) > 300:
                return False
            signed_data = timestamp
            for key in sorted(payload.keys()):
                signed_data += str(key) + str(payload[key])
            expected = hmac.new(secret_key.encode(), signed_data.encode(), hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected, received_sig)
        except Exception:
            return False

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        phone = str(phone).strip().replace(" ", "").replace("-", "")
        if phone.startswith("+"): phone = phone[1:]
        if phone.startswith("0"): phone = "256" + phone[1:]
        if not phone.startswith("256"): phone = "256" + phone
        return phone
