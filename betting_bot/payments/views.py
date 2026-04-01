import json
import logging
from urllib.parse import parse_qs

from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.conf import settings

from packages.models import Package
from .models import Payment
from .services import initiate_payment, initiate_yoo_payment, initiate_live_payment, confirm_payment, initiate_web_payment
from .yoo_client import restore_reference

logger = logging.getLogger(__name__)

SUCCESS_STATUSES = {"completed", "success", "successful", "paid"}


def verify_webhook_token(request):
    secret = getattr(settings, "WEBHOOK_SECRET_TOKEN", "")
    if not secret:
        return True
    token = request.GET.get("token") or request.headers.get("X-Webhook-Token", "")
    return token == secret


@csrf_exempt
def initiate_payment_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    phone = data.get("phone")
    package_id = data.get("package_id")
    user_id = data.get("user_id")

    if not all([phone, package_id, user_id]):
        return HttpResponseBadRequest("Missing required fields: phone, package_id, user_id")

    try:
        user = User.objects.get(id=user_id)
        package = Package.objects.get(id=package_id)
    except (User.DoesNotExist, Package.DoesNotExist):
        return HttpResponseBadRequest("Invalid user or package")

    try:
        payment = initiate_payment(user=user, package=package, phone=phone)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({
        "success": True,
        "payment_id": payment.id,
        "reference": payment.reference,
        "status": payment.status,
        "amount": str(payment.amount),
        "message": "Please approve the payment on your phone."
    })


@csrf_exempt
def initiate_yoo_payment_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    phone = data.get("phone")
    package_id = data.get("package_id")
    user_id = data.get("user_id")

    if not all([phone, package_id, user_id]):
        return HttpResponseBadRequest("Missing required fields: phone, package_id, user_id")

    try:
        user = User.objects.get(id=user_id)
        package = Package.objects.get(id=package_id)
    except (User.DoesNotExist, Package.DoesNotExist):
        return HttpResponseBadRequest("Invalid user or package")

    try:
        payment = initiate_yoo_payment(user=user, package=package, phone=phone)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({
        "success": True,
        "payment_id": payment.id,
        "reference": payment.reference,
        "status": payment.status,
        "amount": str(payment.amount),
        "message": "Please approve the payment on your phone.",
    })


@csrf_exempt
def makypay_webhook(request):
    if not verify_webhook_token(request):
        return HttpResponse(status=403)

    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    logger.info(f"MakyPay webhook received: body={request.body}, content_type={request.content_type}")

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from MakyPay: {request.body}")
        return HttpResponseBadRequest("Invalid JSON")

    transaction = payload.get("transaction", {})
    event_type = payload.get("event_type", "")
    reference = transaction.get("reference")
    status = (transaction.get("status") or "").lower().strip()
    external_reference = transaction.get("uuid")

    if not reference or not status:
        logger.warning(f"Missing fields in webhook: reference={reference}, status={status}")
        return HttpResponseBadRequest("Missing required fields: reference, status")

    if status in SUCCESS_STATUSES or event_type == "collection.completed":
        try:
            confirm_payment(reference=reference, external_reference=external_reference)
            try:
                payment = Payment.objects.get(reference=reference)
                if payment.delivery_channel == Payment.CHANNEL_TELEGRAM:
                    from bots.notifications import notify_payment_success
                    notify_payment_success(payment.user, payment.package, payment)
            except Exception as e:
                logger.error(f"Failed to send success notification: {e}")
        except Payment.DoesNotExist:
            return JsonResponse({"success": False, "error": "Unknown reference"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        return JsonResponse({"success": True})

    elif status == "failed" or event_type == "collection.failed":
        try:
            payment = Payment.objects.get(reference=reference)
            payment.status = Payment.STATUS_FAILED
            payment.external_reference = external_reference
            payment.save()
            try:
                from bots.notifications import notify_payment_failed
                notify_payment_failed(payment.user, payment.package, payment)
            except Exception as e:
                logger.error(f"Failed to send failure notification: {e}")
        except Payment.DoesNotExist:
            logger.error(f"Unknown reference for failed payment: {reference}")
        return JsonResponse({"message": "Payment failed", "status": "acknowledged"}, status=200)

    return JsonResponse({"message": "Ignored"}, status=200)


@csrf_exempt
def yoo_ipn(request):
    if not verify_webhook_token(request):
        return HttpResponse(status=403)

    if request.method != "POST":
        return HttpResponse("OK")

    try:
        params = {k: v[0] for k, v in parse_qs(request.body.decode("utf-8")).items()}
    except Exception as e:
        logger.error("Yoo IPN parse error: %s", e)
        return HttpResponse("OK")

    logger.info("Yoo IPN received: %s", params)

    raw_ref = params.get("external_ref", "")
    network_ref = params.get("network_ref", "")
    msisdn = params.get("msisdn", "")

    if not raw_ref or not network_ref or not msisdn:
        logger.warning("Yoo IPN missing fields: %s", params)
        return HttpResponse("OK")

    reference = restore_reference(raw_ref)

    try:
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            # Check if this is an SMS top-up reference first
            # Search both with and without hyphens since make_reference() stores hex
            from payments.models import SMSTopUp, SMSBalance
            topup = (
                SMSTopUp.objects.filter(payment_reference=raw_ref).first()
                or SMSTopUp.objects.filter(payment_reference=reference).first()
            )
            if topup:
                if topup.status == SMSTopUp.STATUS_SUCCESS:
                    return HttpResponse("OK")
                topup.status = SMSTopUp.STATUS_SUCCESS
                topup.save(update_fields=["status"])
                balance = SMSBalance.get()
                balance.credits += topup.credits_added
                balance.save(update_fields=["credits", "updated_at"])
                return HttpResponse("OK")

            payment = (
                Payment.objects.select_for_update().filter(reference=raw_ref).first()
                or Payment.objects.select_for_update().get(reference=reference)
            )
            if payment.status == Payment.STATUS_SUCCESS:
                return HttpResponse("OK")
            confirm_payment(reference=payment.reference, external_reference=network_ref)
        try:
            payment.refresh_from_db()
            if payment.delivery_channel == Payment.CHANNEL_TELEGRAM:
                from bots.notifications import notify_payment_success
                notify_payment_success(payment.user, payment.package, payment)
        except Exception as e:
            logger.error("Yoo IPN notification error: %s", e)
    except Payment.DoesNotExist:
        logger.error("Yoo IPN unknown reference: %s", reference)
    except Exception as e:
        logger.error("Yoo IPN error: %s", e)

    return HttpResponse("OK")


@csrf_exempt
def yoo_failure_ipn(request):
    if not verify_webhook_token(request):
        return HttpResponse(status=403)

    if request.method != "POST":
        return HttpResponse("OK")

    try:
        params = {k: v[0] for k, v in parse_qs(request.body.decode("utf-8")).items()}
    except Exception as e:
        logger.error("Yoo failure IPN parse error: %s", e)
        return HttpResponse("OK")

    raw_ref = params.get("failed_transaction_reference", "")
    if not raw_ref:
        return HttpResponse("OK")

    reference = restore_reference(raw_ref)

    try:
        from django.db import transaction as db_transaction
        with db_transaction.atomic():
            from payments.models import SMSTopUp
            topup = (
                SMSTopUp.objects.filter(payment_reference=raw_ref).first()
                or SMSTopUp.objects.filter(payment_reference=reference).first()
            )
            if topup:
                if topup.status == SMSTopUp.STATUS_PENDING:
                    topup.status = SMSTopUp.STATUS_FAILED
                    topup.save(update_fields=["status"])
                return HttpResponse("OK")

            payment = (
                Payment.objects.select_for_update().filter(reference=raw_ref).first()
                or Payment.objects.select_for_update().get(reference=reference)
            )
            if payment.status != Payment.STATUS_PENDING:
                return HttpResponse("OK")
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=["status"])
        try:
            from bots.notifications import notify_payment_failed
            notify_payment_failed(payment.user, payment.package, payment)
        except Exception as e:
            logger.error("Yoo failure IPN notification error: %s", e)
    except Payment.DoesNotExist:
        logger.error("Yoo failure IPN unknown reference: %s", reference)
    except Exception as e:
        logger.error("Yoo failure IPN error: %s", e)

    return HttpResponse("OK")


def payment_status(request, reference):
    from payments.models import SMSTopUp
    topup = SMSTopUp.objects.filter(payment_reference=reference).first()
    if topup:
        return JsonResponse({
            "success": True,
            "reference": reference,
            "status": topup.status,
            "credits_added": topup.credits_added if topup.status == SMSTopUp.STATUS_SUCCESS else 0,
        })

    try:
        payment = Payment.objects.get(reference=reference)
    except Payment.DoesNotExist:
        return HttpResponseBadRequest("Invalid reference")

    # For LivePay pending payments, poll LivePay directly
    if payment.status == Payment.STATUS_PENDING and payment.provider_type == Payment.PROVIDER_LIVE:
        try:
            from .models import LivePayProvider
            from .live_client import LivePayClient
            provider = LivePayProvider.objects.filter(is_active=True).first()
            if provider and payment.external_reference:
                client = LivePayClient(public_key=provider.public_key, secret_key=provider.secret_key)
                result = client.check_status(payment.external_reference)
                logger.warning("LIVEPAY STATUS POLL ref=%s result=%s", reference, result)
                status_val = str(result.get("status", "")).lower()
                txn_status = str(result.get("data", {}).get("status", "")).lower()
                if status_val == "success" and txn_status in ("approved", "success", "completed"):
                    confirm_payment(reference=payment.reference, external_reference=payment.external_reference)
                    payment.refresh_from_db()
                elif txn_status in ("failed", "cancelled"):
                    payment.status = Payment.STATUS_FAILED
                    payment.save(update_fields=["status"])
        except Exception as e:
            logger.error("LivePay status poll error ref=%s: %s", reference, e)

    return JsonResponse({
        "success": True,
        "reference": payment.reference,
        "status": payment.status,
        "subscription_created": payment.status == Payment.STATUS_SUCCESS
    })


@csrf_exempt
def landing_initiate_payment(request):
    """Called by the landing page - creates user from phone, initiates payment via active provider."""
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    phone = (data.get("phone") or "").strip()
    package_id = data.get("package_id")

    if not phone or not package_id:
        return JsonResponse({"success": False, "error": "Phone and package are required."}, status=400)

    try:
        payment = initiate_web_payment(phone=phone, package_id=int(package_id))
    except Package.DoesNotExist:
        return JsonResponse({"success": False, "error": "Package not found."}, status=404)
    except Exception as e:
        logger.error("Landing payment error: %s", e)
        return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({
        "success": True,
        "reference": payment.reference,
        "amount": str(payment.amount),
        "message": "USSD prompt sent. Please approve on your phone to complete payment."
    })


@csrf_exempt
def initiate_live_payment_view(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    try:
        data = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    phone = data.get("phone")
    package_id = data.get("package_id")
    user_id = data.get("user_id")

    if not all([phone, package_id, user_id]):
        return HttpResponseBadRequest("Missing required fields: phone, package_id, user_id")

    try:
        user = User.objects.get(id=user_id)
        package = Package.objects.get(id=package_id)
    except (User.DoesNotExist, Package.DoesNotExist):
        return HttpResponseBadRequest("Invalid user or package")

    try:
        payment = initiate_live_payment(user=user, package=package, phone=phone)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({
        "success": True,
        "payment_id": payment.id,
        "reference": payment.reference,
        "status": payment.status,
        "amount": str(payment.amount),
        "message": "USSD prompt sent. Please approve on your phone.",
    })


@csrf_exempt
def live_ipn(request):
    """POST /pay/webhook/live/ipn/ — LivePay webhook.
    Payload fields: status, transaction_id, reference_id, phone, amount, payment_method, charge_amount
    Header: livepay-signature: t=TIMESTAMP,v=SIGNATURE
    """
    if request.method != "POST":
        return HttpResponse("OK")

    try:
        data = json.loads(request.body.decode("utf-8", errors="replace"))
    except Exception:
        data = {}

    logger.warning("LIVEPAY IPN received: %s", data)

    # Verify signature
    from .models import LivePayProvider
    from .live_client import LivePayClient
    provider = LivePayProvider.objects.filter(is_active=True).first()
    if provider:
        sig_header = request.headers.get("livepay-signature", "")
        if sig_header and not LivePayClient.verify_webhook_signature(provider.secret_key, sig_header, data):
            logger.warning("LIVEPAY IPN: signature mismatch — processing anyway for now")

    # Fields per LivePay docs
    status = str(data.get("status", "")).strip()       # Approved / Failed / Pending / Cancelled
    transaction_id = data.get("transaction_id", "")    # LivePay transaction ID
    reference_id = data.get("reference_id", "")        # our original reference

    if not reference_id:
        logger.warning("LIVEPAY IPN: no reference_id — ignoring")
        return HttpResponse(json.dumps({"status": "received", "message": "Webhook processed successfully"}), content_type="application/json")

    is_success = status.lower() == "approved"
    is_failed = status.lower() in ("failed", "cancelled")

    if is_success:
        try:
            payment = Payment.objects.filter(reference=reference_id).first()
            if not payment:
                logger.warning("LIVEPAY IPN: no payment found for reference_id=%s", reference_id)
                return HttpResponse(json.dumps({"status": "received", "message": "Webhook processed successfully"}), content_type="application/json")
            if payment.status == Payment.STATUS_SUCCESS:
                return HttpResponse(json.dumps({"status": "received", "message": "Webhook processed successfully"}), content_type="application/json")
            confirm_payment(reference=payment.reference, external_reference=transaction_id)
            logger.warning("LIVEPAY IPN: payment confirmed ref=%s", reference_id)
            try:
                payment.refresh_from_db()
                if payment.delivery_channel == Payment.CHANNEL_TELEGRAM:
                    from bots.notifications import notify_payment_success
                    notify_payment_success(payment.user, payment.package, payment)
            except Exception as e:
                logger.error("LIVEPAY IPN notification error: %s", e)
        except Exception as e:
            logger.error("LIVEPAY IPN error: %s", e)

    elif is_failed:
        try:
            payment = Payment.objects.filter(reference=reference_id).first()
            if payment and payment.status == Payment.STATUS_PENDING:
                payment.status = Payment.STATUS_FAILED
                payment.external_reference = transaction_id
                payment.save(update_fields=["status", "external_reference"])
                try:
                    from bots.notifications import notify_payment_failed
                    notify_payment_failed(payment.user, payment.package, payment)
                except Exception as e:
                    logger.error("LIVEPAY IPN failure notification error: %s", e)
        except Exception as e:
            logger.error("LIVEPAY IPN failed handler error: %s", e)

    return HttpResponse(json.dumps({"status": "received", "message": "Webhook processed successfully"}), content_type="application/json")
