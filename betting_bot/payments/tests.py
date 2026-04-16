from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth.models import User

from payments.models import (
    LivePayProvider, KwaPayProvider, YooPaymentProvider,
    OwnerWallet, WithdrawalRequest, SMSBalance, SMSTopUp,
)


def _make_live(is_active=True):
    return LivePayProvider.objects.create(
        public_key="LP123", secret_key="sk_live", is_active=is_active,
        withdrawal_fee=Decimal("0"), gateway_fee_percentage=Decimal("0"),
    )


def _make_kwa(is_active=True):
    return KwaPayProvider.objects.create(
        primary_api="kwa_primary", secondary_api="kwa_secondary",
        callback_url="https://example.com/kwa/cb", is_active=is_active,
        withdrawal_fee=Decimal("0"),
    )


def _make_yoo(is_active=True):
    return YooPaymentProvider.objects.create(
        api_username="yoo_user", api_password="yoo_pass",
        notification_url="https://example.com/yoo/notify",
        failure_url="https://example.com/yoo/fail",
        is_active=is_active,
    )


def _make_wallet(balance=50000):
    wallet, _ = OwnerWallet.objects.get_or_create(pk=1)
    wallet.balance = Decimal(str(balance))
    wallet.save()
    return wallet


# ---------------------------------------------------------------------------
# wallet_withdraw  (uses Django test Client — needs session middleware)
# ---------------------------------------------------------------------------

class WalletWithdrawLivePayTest(TestCase):
    def setUp(self):
        self.provider = _make_live()
        _make_wallet(50000)
        self.user = User.objects.create_user("owner", password="pass", is_staff=True)
        self.client.force_login(self.user)

    @patch("payments.livepay_client.LivePayClient.send", return_value={"success": True, "message": "OK"})
    def test_livepay_success_deducts_wallet(self, mock_send):
        self.client.post("/dashboard/wallet/withdraw/", {"phone": "0771234567", "amount": "10000"})
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("40000"))
        wr = WithdrawalRequest.objects.first()
        self.assertEqual(wr.status, WithdrawalRequest.STATUS_PAID)

    @patch("payments.livepay_client.LivePayClient.send", return_value={"success": False, "message": "Rejected"})
    def test_livepay_failure_marks_failed(self, mock_send):
        self.client.post("/dashboard/wallet/withdraw/", {"phone": "0771234567", "amount": "10000"})
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("50000"))  # unchanged
        wr = WithdrawalRequest.objects.first()
        self.assertEqual(wr.status, WithdrawalRequest.STATUS_FAILED)
        self.assertEqual(wr.failure_reason, "Rejected")


class WalletWithdrawKwaPayTest(TestCase):
    def setUp(self):
        self.provider = _make_kwa()
        _make_wallet(50000)
        self.user = User.objects.create_user("owner", password="pass", is_staff=True)
        self.client.force_login(self.user)

    @patch("payments.kwa_client.KwaPayClient.withdraw", return_value={"error": False, "message": "OK"})
    def test_kwapay_success_deducts_wallet(self, mock_withdraw):
        self.client.post("/dashboard/wallet/withdraw/", {"phone": "0771234567", "amount": "10000"})
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("40000"))
        wr = WithdrawalRequest.objects.first()
        self.assertEqual(wr.status, WithdrawalRequest.STATUS_PAID)

    @patch("payments.kwa_client.KwaPayClient.withdraw", return_value={"error": True, "message": "Failed"})
    def test_kwapay_failure_marks_failed(self, mock_withdraw):
        self.client.post("/dashboard/wallet/withdraw/", {"phone": "0771234567", "amount": "10000"})
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("50000"))  # unchanged
        wr = WithdrawalRequest.objects.first()
        self.assertEqual(wr.status, WithdrawalRequest.STATUS_FAILED)


class WalletWithdrawYooTest(TestCase):
    def setUp(self):
        self.provider = _make_yoo()
        _make_wallet(50000)
        self.user = User.objects.create_user("owner", password="pass", is_staff=True)
        self.client.force_login(self.user)

    @patch("payments.yoo_client.YooClient.disburse", return_value={"yoo_status": "SUCCESS"})
    def test_yoo_success_deducts_wallet(self, mock_disburse):
        self.client.post("/dashboard/wallet/withdraw/", {"phone": "0771234567", "amount": "10000"})
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("40000"))
        wr = WithdrawalRequest.objects.first()
        self.assertEqual(wr.status, WithdrawalRequest.STATUS_PAID)

    @patch("payments.yoo_client.YooClient.disburse", return_value={"yoo_status": "FAILED", "error_message": "Insufficient funds"})
    def test_yoo_failure_marks_failed(self, mock_disburse):
        self.client.post("/dashboard/wallet/withdraw/", {"phone": "0771234567", "amount": "10000"})
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("50000"))  # unchanged
        wr = WithdrawalRequest.objects.first()
        self.assertEqual(wr.status, WithdrawalRequest.STATUS_FAILED)


class WalletWithdrawNoProviderTest(TestCase):
    def setUp(self):
        _make_wallet(50000)
        self.user = User.objects.create_user("owner", password="pass", is_staff=True)
        self.client.force_login(self.user)

    def test_no_provider_returns_error(self):
        self.client.post("/dashboard/wallet/withdraw/", {"phone": "0771234567", "amount": "10000"})
        self.assertEqual(WithdrawalRequest.objects.count(), 0)
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("50000"))  # unchanged


# ---------------------------------------------------------------------------
# owner_withdraw (JSON API)
# ---------------------------------------------------------------------------

class OwnerWithdrawTest(TestCase):
    def setUp(self):
        _make_wallet(100000)
        self.user = User.objects.create_user("owner", password="pass", is_staff=True)
        self.client.force_login(self.user)

    def _post(self, data):
        import json
        return self.client.post(
            "/dashboard/wallet/owner-withdraw/",
            data=json.dumps(data),
            content_type="application/json",
        )

    @patch("payments.live_client.LivePayClient.send", return_value={"success": True})
    def test_livepay_owner_withdraw_success(self, mock_send):
        import json
        _make_live()
        resp = self._post({"phone": "0771234567", "amount": "20000", "network": "MTN"})
        data = json.loads(resp.content)
        self.assertTrue(data["success"])
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("80000"))
        self.assertEqual(WithdrawalRequest.objects.filter(status=WithdrawalRequest.STATUS_PAID).count(), 1)

    @patch("payments.kwa_client.KwaPayClient.withdraw", return_value={"error": False})
    def test_kwapay_owner_withdraw_success(self, mock_withdraw):
        import json
        _make_kwa()
        resp = self._post({"phone": "0771234567", "amount": "20000", "network": "MTN"})
        data = json.loads(resp.content)
        self.assertTrue(data["success"])
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("80000"))

    @patch("payments.yoo_client.YooClient.disburse", return_value={"yoo_status": "SUCCESS"})
    def test_yoo_owner_withdraw_success(self, mock_disburse):
        import json
        _make_yoo()
        resp = self._post({"phone": "0771234567", "amount": "20000", "network": "MTN"})
        data = json.loads(resp.content)
        self.assertTrue(data["success"])
        wallet = OwnerWallet.objects.get(pk=1)
        self.assertEqual(wallet.balance, Decimal("80000"))

    def test_insufficient_balance_rejected(self):
        import json
        _make_live()
        resp = self._post({"phone": "0771234567", "amount": "999999", "network": "MTN"})
        data = json.loads(resp.content)
        self.assertFalse(data["success"])
        self.assertIn("Insufficient", data["error"])

    def test_below_minimum_rejected(self):
        import json
        _make_live()
        resp = self._post({"phone": "0771234567", "amount": "5000", "network": "MTN"})
        data = json.loads(resp.content)
        self.assertFalse(data["success"])
        self.assertIn("10,000", data["error"])


# ---------------------------------------------------------------------------
# sms_topup_pay
# ---------------------------------------------------------------------------

class SmsTopupPayTest(TestCase):
    def setUp(self):
        bal, _ = SMSBalance.objects.get_or_create(pk=1)
        bal.price_per_sms = Decimal("100")
        bal.save()
        self.user = User.objects.create_user("owner", password="pass", is_staff=True)
        self.client.force_login(self.user)

    def _post(self, data):
        import json
        return self.client.post(
            "/dashboard/sms-credits/pay/",
            data=json.dumps(data),
            content_type="application/json",
        )

    @patch("payments.kwa_client.KwaPayClient.collect", return_value={"error": False, "internal_reference": "kwa_ref_1"})
    def test_kwapay_topup_creates_pending(self, mock_collect):
        import json
        _make_kwa()
        resp = self._post({"phone": "0771234567", "amount": 5000})
        data = json.loads(resp.content)
        self.assertTrue(data["success"])
        self.assertEqual(data["credits"], 50)
        topup = SMSTopUp.objects.first()
        self.assertEqual(topup.status, SMSTopUp.STATUS_PENDING)
        self.assertEqual(topup.credits_added, 50)

    @patch("payments.livepay_client.LivePayClient.collect", return_value={"status": "pending"})
    def test_livepay_topup_creates_pending(self, mock_collect):
        import json
        _make_live()
        resp = self._post({"phone": "0771234567", "amount": 5000})
        data = json.loads(resp.content)
        self.assertTrue(data["success"])
        topup = SMSTopUp.objects.first()
        self.assertEqual(topup.status, SMSTopUp.STATUS_PENDING)

    @patch("payments.yoo_client.YooClient.collect", return_value={"yoo_status": "PENDING"})
    def test_yoo_topup_creates_pending(self, mock_collect):
        import json
        _make_yoo()
        resp = self._post({"phone": "0771234567", "amount": 5000})
        data = json.loads(resp.content)
        self.assertTrue(data["success"])
        topup = SMSTopUp.objects.first()
        self.assertEqual(topup.status, SMSTopUp.STATUS_PENDING)

    @patch("payments.kwa_client.KwaPayClient.collect", return_value={"error": True, "message": "Bad request"})
    def test_kwapay_topup_failure_marks_failed(self, mock_collect):
        import json
        _make_kwa()
        resp = self._post({"phone": "0771234567", "amount": 5000})
        data = json.loads(resp.content)
        self.assertFalse(data["success"])
        topup = SMSTopUp.objects.first()
        self.assertEqual(topup.status, SMSTopUp.STATUS_FAILED)

    def test_no_provider_returns_error(self):
        import json
        resp = self._post({"phone": "0771234567", "amount": 5000})
        data = json.loads(resp.content)
        self.assertFalse(data["success"])
        self.assertIn("No payment provider", data["error"])

    def test_below_minimum_credits_rejected(self):
        import json
        _make_kwa()
        resp = self._post({"phone": "0771234567", "amount": 50})  # less than price_per_sms=100
        data = json.loads(resp.content)
        self.assertFalse(data["success"])
        self.assertIn("Minimum", data["error"])

    # KwaPay takes priority over LivePay when both active
    @patch("payments.kwa_client.KwaPayClient.collect", return_value={"error": False})
    @patch("payments.livepay_client.LivePayClient.collect", return_value={"status": "pending"})
    def test_kwapay_takes_priority_over_livepay(self, mock_live, mock_kwa):
        _make_kwa()
        _make_live()
        self._post({"phone": "0771234567", "amount": 5000})
        mock_kwa.assert_called_once()
        mock_live.assert_not_called()
