from payments.models import SMSBalance, Payment
from predictions.models import Prediction
from subscription.models import Subscription
from django.utils import timezone

print("=== SMS BALANCE ===")
b = SMSBalance.get()
print(f"  credits: {b.credits}")

print("\n=== RECENT NEW SUBSCRIBERS (last 24hrs) ===")
from datetime import timedelta
since = timezone.now() - timedelta(hours=24)
recent_payments = Payment.objects.filter(
    status=Payment.STATUS_SUCCESS,
    created_at__gte=since
).select_related("user", "package").order_by("-created_at")
for p in recent_payments:
    print(f"  {p.phone} | {p.package.name} | {p.created_at.strftime('%H:%M')}")

    today = timezone.localtime(timezone.now()).date()
    preds = Prediction.objects.filter(
        is_active=True, is_sent=True,
        send_date=today, package=p.package
    )
    latest = Prediction.objects.filter(
        is_active=True, is_sent=True, package=p.package
    ).order_by('-send_date').first()

    print(f"    Today predictions: {preds.count()}")
    print(f"    Latest prediction date: {latest.send_date if latest else 'NONE'}")
