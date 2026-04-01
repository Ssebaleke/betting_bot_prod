import uuid
import requests
import xml.etree.ElementTree as ET


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
    """UUID without hyphens — Yo! rejects hyphens (error -7)."""
    return uuid.uuid4().hex


def restore_reference(ref: str) -> str:
    """Restore hyphens to a 32-char hex UUID."""
    if len(ref) == 32:
        return f"{ref[:8]}-{ref[8:12]}-{ref[12:16]}-{ref[16:20]}-{ref[20:]}"
    return ref


class YooClient:
    PRIMARY = "https://paymentsapi1.yo.co.ug/ybs/task.php"
    BACKUP = "https://paymentsapi2.yo.co.ug/ybs/task.php"
    TIMEOUT = 30

    SUCCESS_STATUSES = {"SUCCEEDED", "SUCCESS", "SUCCESSFUL", "COMPLETED", "APPROVED"}
    FAILED_STATUSES = {"FAILED", "CANCELLED", "REJECTED", "EXPIRED"}

    def __init__(self, api_username: str, api_password: str):
        self.api_username = api_username
        self.api_password = api_password

    def _build_root(self, method: str) -> ET.Element:
        root = ET.Element("AutoCreate")
        req = ET.SubElement(root, "Request")
        ET.SubElement(req, "APIUsername").text = self.api_username
        ET.SubElement(req, "APIPassword").text = self.api_password
        ET.SubElement(req, "Method").text = method
        return root

    def _post(self, xml_root: ET.Element) -> ET.Element:
        import concurrent.futures
        body = '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(xml_root, encoding="unicode")
        headers = {"Content-Type": "text/xml"}
        encoded = body.encode("utf-8")

        def try_url(url):
            r = requests.post(url, data=encoded, headers=headers, timeout=self.TIMEOUT)
            r.raise_for_status()
            return ET.fromstring(r.text)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = {executor.submit(try_url, url): url for url in (self.PRIMARY, self.BACKUP)}
            for future in concurrent.futures.as_completed(futures, timeout=self.TIMEOUT + 5):
                try:
                    return future.result()
                except Exception:
                    continue
        raise ValueError("Yo! API unreachable on both endpoints")

    def _parse(self, tree: ET.Element) -> dict:
        resp = tree.find("Response") or tree
        return {
            "status": (resp.findtext("Status") or "").upper(),
            "status_code": resp.findtext("StatusCode") or "",
            "status_message": resp.findtext("StatusMessage") or "",
            "transaction_status": (resp.findtext("TransactionStatus") or "").upper(),
            "transaction_reference": resp.findtext("TransactionReference") or "",
            "error_message": resp.findtext("ErrorMessage") or "",
            "error_code": resp.findtext("ErrorMessageCode") or "",
        }

    def classify(self, parsed: dict) -> str:
        """Returns 'SUCCESS', 'PENDING', or 'FAILED'."""
        ts = parsed["transaction_status"]
        if ts in self.SUCCESS_STATUSES:
            return "SUCCESS"
        if ts in self.FAILED_STATUSES:
            return "FAILED"
        if parsed["status"] == "OK" and parsed["status_code"] == "0":
            return "SUCCESS"
        if parsed["status"] == "OK" and parsed["status_code"] == "1":
            return "PENDING"
        if parsed["status"] == "ERROR":
            return "FAILED"
        return "PENDING"

    def collect(self, phone: str, amount, reference: str, notification_url: str, failure_url: str, narrative: str = "Subscription payment") -> dict:
        root = self._build_root("acdepositfunds")
        req = root.find("Request")
        ET.SubElement(req, "NonBlocking").text = "TRUE"
        ET.SubElement(req, "Amount").text = str(int(amount))
        ET.SubElement(req, "Account").text = normalize_phone(phone)
        ET.SubElement(req, "Narrative").text = narrative
        ET.SubElement(req, "ExternalReference").text = reference
        ET.SubElement(req, "InstantNotificationUrl").text = notification_url
        ET.SubElement(req, "FailureNotificationUrl").text = failure_url
        parsed = self._parse(self._post(root))
        parsed["yoo_status"] = self.classify(parsed)
        return parsed

    def disburse(self, phone: str, amount, reference: str, narrative: str = "Payout") -> dict:
        root = self._build_root("acwithdrawfunds")
        req = root.find("Request")
        ET.SubElement(req, "NonBlocking").text = "TRUE"
        ET.SubElement(req, "Amount").text = str(int(amount))
        ET.SubElement(req, "Account").text = normalize_phone(phone)
        ET.SubElement(req, "Narrative").text = narrative
        ET.SubElement(req, "InternalReference").text = reference
        ET.SubElement(req, "ExternalReference").text = reference
        parsed = self._parse(self._post(root))
        parsed["yoo_status"] = self.classify(parsed)
        return parsed

    def balance(self) -> dict:
        parsed = self._parse(self._post(self._build_root("acacctbalance")))
        return parsed

    def check_status(self, reference: str) -> dict:
        root = self._build_root("actransactioncheckstatus")
        req = root.find("Request")
        ET.SubElement(req, "PrivateTransactionReference").text = reference
        parsed = self._parse(self._post(root))
        parsed["yoo_status"] = self.classify(parsed)
        return parsed
