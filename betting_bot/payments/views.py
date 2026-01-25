import json
from decimal import Decimal

from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from packages.models import Package
from .models import Payment
from .services import initiate_payment, confirm_payment


@csrf_exempt
def initiate_payment_view(request):
    """
    Initiate MakyPay request-to-pay
    """
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method")

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    phone = data.get("phone")
    package_id = data.get("package_id")
    user_id = data.get("user_id")

    if not all([phone, package_id, user_id]):
        return HttpResponseBadRequest("Missing required fields")

    try:
        user = User.objects.get(id=user_id)
        package = Package.objects.get(id=package_id)
    except (User.DoesNotExist, Package.DoesNotExist):
        return HttpResponseBadRequest("Invalid user or package")

    payment = initiate_payment(
        user=user,
        package=package,
        phone=phone
    )

    return JsonResponse({
        "success": True,
        "reference": payment.reference,
        "status": payment.status,
        "amount": str(payment.amount),
        "message": "Please approve the payment on your phone"
    })


@csrf_exempt
def makypay_webhook(request):
    """
    Webhook called by MakyPay Wire-API
    """
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    reference = payload.get("reference")
    status = payload.get("status")
    external_reference = payload.get("external_reference")

    if not reference or not status:
        return HttpResponseBadRequest("Missing required fields")

    # MakyPay sends "completed" on success
    if status != "completed":
        return JsonResponse({"message": "Ignored"}, status=200)

    confirm_payment(
        reference=reference,
        external_reference=external_reference
    )

    return JsonResponse({"success": True})


def payment_status(request, reference):
    """
    Poll payment status
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
