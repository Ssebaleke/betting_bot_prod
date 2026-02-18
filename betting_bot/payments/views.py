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
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    reference = payload.get("reference")
    status = (payload.get("status") or "").lower().strip()
    external_reference = payload.get("external_reference")

    if not reference or not status:
        return HttpResponseBadRequest("Missing required fields: reference, status")

    if status not in SUCCESS_STATUSES:
        return JsonResponse({"message": "Ignored"}, status=200)

    try:
        confirm_payment(reference=reference, external_reference=external_reference)
    except Payment.DoesNotExist:
        return JsonResponse({"success": False, "error": "Unknown reference"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": True})


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
