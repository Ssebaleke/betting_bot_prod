import json

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from packages.models import Package
from .models import Payment
from .services import initiate_payment, confirm_payment


SUCCESS_STATUSES = {"completed", "success", "successful", "paid"}


@csrf_exempt
def initiate_payment_view(request):
    """
    Initiate MakyPay request-to-pay

    POST JSON:
    {
      "phone": "0708826558",
      "package_id": 1,
      "user_id": 10
    }
    """
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
def makypay_webhook(request):
    """
    Webhook called by MakyPay Wire-API
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    # Log raw request for debugging
    logger.info(f"MakyPay webhook received: body={request.body}, content_type={request.content_type}")
    
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON from MakyPay: {request.body}")
        return HttpResponseBadRequest("Invalid JSON")

    logger.info(f"MakyPay webhook payload: {payload}")
    
    # MakyPay sends data in nested structure
    transaction = payload.get("transaction", {})
    event_type = payload.get("event_type", "")
    
    reference = transaction.get("reference")
    status = (transaction.get("status") or "").lower().strip()
    external_reference = transaction.get("uuid")  # MakyPay's transaction UUID

    if not reference or not status:
        logger.warning(f"Missing fields in webhook: reference={reference}, status={status}")
        return HttpResponseBadRequest("Missing required fields: reference, status")
    
    logger.info(f"Processing webhook: event={event_type}, reference={reference}, status={status}")

    # Handle success events
    if status in SUCCESS_STATUSES or event_type == "collection.completed":
        try:
            confirm_payment(reference=reference, external_reference=external_reference)
            logger.info(f"Payment confirmed: {reference}")
            
            # Send success notification
            try:
                from bots.notifications import notify_payment_success
                payment = Payment.objects.get(reference=reference)
                notify_payment_success(payment.user, payment.package, payment)
            except Exception as e:
                logger.error(f"Failed to send success notification: {e}")
                
        except Payment.DoesNotExist:
            logger.error(f"Unknown reference: {reference}")
            return JsonResponse({"success": False, "error": "Unknown reference"}, status=404)
        except Exception as e:
            logger.error(f"Error confirming payment: {e}")
            return JsonResponse({"success": False, "error": str(e)}, status=400)
        
        return JsonResponse({"success": True})
    
    # Handle failed events
    elif status == "failed" or event_type == "collection.failed":
        try:
            payment = Payment.objects.get(reference=reference)
            payment.status = Payment.STATUS_FAILED
            payment.external_reference = external_reference
            payment.save()
            logger.info(f"Payment marked as failed: {reference}")
            
            # Send failure notification
            try:
                from bots.notifications import notify_payment_failed
                notify_payment_failed(payment.user, payment.package, payment)
            except Exception as e:
                logger.error(f"Failed to send failure notification: {e}")
                
        except Payment.DoesNotExist:
            logger.error(f"Unknown reference for failed payment: {reference}")
        return JsonResponse({"message": "Payment failed", "status": "acknowledged"}, status=200)
    
    # Ignore other statuses
    else:
        logger.info(f"Ignoring status: {status}")
        return JsonResponse({"message": "Ignored"}, status=200)


def payment_status(request, reference):
    """
    Poll payment status (DB).
    """
    try:
        payment = Payment.objects.get(reference=reference)
    except Payment.DoesNotExist:
        return HttpResponseBadRequest("Invalid reference")

    return JsonResponse({
        "success": True,
        "reference": payment.reference,
        "status": payment.status,
        "subscription_created": payment.status == Payment.STATUS_SUCCESS
    })
