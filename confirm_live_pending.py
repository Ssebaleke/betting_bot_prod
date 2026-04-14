from payments.models import Payment
from payments.services import confirm_payment, _post_payment_notifications
from subscription.models import Subscription

pending = Payment.objects.filter(
    status=Payment.STATUS_PENDING,
    provider_type=Payment.PROVIDER_LIVE
).select_related("user", "package").order_by("-created_at")

print(f"Pending LivePay payments: {pending.count()}")
for p in pending:
    print(f"  ref={p.reference} | phone={p.phone} | amount={p.amount} | pkg={p.package.name} | ext_ref={p.external_reference}")
    try:
        confirmed = confirm_payment(reference=p.reference, external_reference=p.external_reference)
        sub = Subscription.objects.filter(user=confirmed.user, is_active=True).order_by("-created_at").first()
        if sub:
            _post_payment_notifications(confirmed.id, sub.id)
        print(f"  ✅ Confirmed! Subscription created.")
    except Exception as e:
        print(f"  ❌ Error: {e}")
