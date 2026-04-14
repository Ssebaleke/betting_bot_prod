from payments.models import Payment
from payments.services import confirm_payment, _post_payment_notifications
from subscription.models import Subscription

# The pending Airtel payment
ref = "583f25416ecd4575a00289a52a10385c"
ext_ref = "TXN1775204575422"

try:
    payment = Payment.objects.get(reference=ref)
    print(f"Payment: {payment.phone} | {payment.package.name} | {payment.amount} | {payment.status}")
    if payment.status == Payment.STATUS_PENDING:
        confirmed = confirm_payment(reference=ref, external_reference=ext_ref)
        sub = Subscription.objects.filter(user=confirmed.user, is_active=True).order_by("-created_at").first()
        if sub:
            _post_payment_notifications(confirmed.id, sub.id)
        print(f"✅ Confirmed! Subscription created for {payment.phone}")
    else:
        print(f"Already {payment.status}")
except Payment.DoesNotExist:
    print("Payment not found")
except Exception as e:
    print(f"Error: {e}")
