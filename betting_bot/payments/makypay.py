import requests


class MakyPayClient:
    def __init__(self, base_url, public_key, secret_key):
        self.base_url = base_url.rstrip("/")
        self.public_key = public_key
        self.secret_key = secret_key

    def request_to_pay(self, phone, amount, reference, webhook_url):
        url = f"{self.base_url}/api/v1/collections/request-to-pay"

        payload = {
            "phone": phone,
            "amount": amount,
            "reference": reference,
            "webhook_url": webhook_url,
        }

        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        return response.json()
