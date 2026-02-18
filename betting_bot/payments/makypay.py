import requests


def normalize_ug_phone(phone: str) -> str:
    """
    Normalize Uganda phone numbers to 2567XXXXXXXX.

    Accepts:
    - 07XXXXXXXX
    - +2567XXXXXXXX
    - 2567XXXXXXXX
    """
    if not phone:
        raise ValueError("Phone number is required")

    p = phone.strip().replace(" ", "")
    if p.startswith("+"):
        p = p[1:]

    # 07XXXXXXXX -> 2567XXXXXXXX
    if p.startswith("0") and len(p) == 10:
        p = "256" + p[1:]

    if not (p.isdigit() and len(p) == 12 and p.startswith("2567")):
        raise ValueError("Invalid UG phone. Use 07XXXXXXXX, +2567XXXXXXXX or 2567XXXXXXXX.")

    return p


class MakyPayClient:
    """
    MakyPay Wire-API client for collections.
    """

    def __init__(self, base_url: str, secret_key: str):
        self.base_url = (base_url or "").rstrip("/")
        self.secret_key = (secret_key or "").strip()

        if not self.base_url:
            raise ValueError("MakyPay base_url is missing")
        if not self.secret_key:
            raise ValueError("MakyPay secret_key is missing")

    def request_to_pay(self, phone_number: str, amount, reference: str, webhook_url: str, currency: str = "UGX"):
        """
        Initiate a collection request (MoMo STK push).
        FIXES:
        - Correct endpoint with trailing slash
        - Correct payload keys (phone_number)
        - Strong timeout to prevent gunicorn hang (connect, read)
        """
        url = f"{self.base_url}/api/v1/collections/request-to-pay/"

        payload = {
            "phone_number": phone_number,  # ✅ correct field
            "amount": amount,
            "reference": reference,
            "webhook_url": webhook_url,
            "currency": currency,
        }

        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

        try:
            # ✅ prevents long hangs that trigger gunicorn WORKER TIMEOUT
            r = requests.post(url, json=payload, headers=headers, timeout=(5, 25))
        except requests.RequestException as e:
            raise ValueError(f"MakyPay request failed: {e}")

        if r.status_code >= 400:
            raise ValueError(f"MakyPay {r.status_code} at {url}: {r.text}")

        return r.json()
