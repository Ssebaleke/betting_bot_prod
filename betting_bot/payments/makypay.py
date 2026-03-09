import requests
import base64


def normalize_ug_phone(phone: str) -> str:
    """
    Normalize Uganda phone numbers to 256XXXXXXXXX (12 digits, no +).
    """
    if not phone:
        raise ValueError("Phone number is required")

    p = phone.strip().replace(" ", "")
    if p.startswith("+"):
        p = p[1:]

    # 07XXXXXXXX -> 256XXXXXXXXX
    if p.startswith("0") and len(p) == 10:
        p = "256" + p[1:]

    if not (p.isdigit() and len(p) == 12 and p.startswith("256")):
        raise ValueError("Invalid UG phone. Use 07XXXXXXXX or 256XXXXXXXXX.")

    return p


class MakyPayClient:
    """
    MakyPay Wire-API client for collections.
    """

    def __init__(self, base_url: str, secret_key: str, public_key: str = ""):
        self.base_url = (base_url or "").rstrip("/")
        self.secret_key = (secret_key or "").strip()
        self.public_key = (public_key or "").strip()

        if not self.base_url:
            raise ValueError("MakyPay base_url is missing")
        if not self.secret_key:
            raise ValueError("MakyPay secret_key is missing")

    def request_to_pay(self, phone_number: str, amount, reference: str, webhook_url: str, currency: str = "UGX"):
        """
        Initiate a collection request (MoMo STK push).
        Uses MakyPay Standard API with Basic Auth and form data.
        """
        url = f"{self.base_url}/api/v1/collections/collect-money"

        # Normalize phone
        phone_number = normalize_ug_phone(phone_number)

        # Form data payload
        payload = {
            "phone_number": phone_number,
            "amount": int(amount),
            "country": "UG",
            "reference": reference,
            "description": "Betting subscription payment",
            "callback_url": webhook_url,
        }

        # Basic Auth with Base64
        if self.public_key:
            credentials = f"{self.public_key}:{self.secret_key}"
        else:
            # If only secret_key provided, assume it's already the base64 header
            credentials = self.secret_key
        
        if ":" in credentials:
            auth_header = base64.b64encode(credentials.encode()).decode()
        else:
            auth_header = credentials

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        print(f"\n=== MakyPay Request ===")
        print(f"URL: {url}")
        print(f"Payload: {payload}")
        print(f"Auth: Basic {auth_header[:20]}...")

        try:
            r = requests.post(url, data=payload, headers=headers, timeout=(5, 25))
            print(f"Response Status: {r.status_code}")
            print(f"Response Body: {r.text}")
        except requests.RequestException as e:
            print(f"Request Exception: {e}")
            raise ValueError(f"MakyPay request failed: {e}")

        if r.status_code >= 400:
            raise ValueError(f"MakyPay {r.status_code} at {url}: {r.text}")

        return r.json()
