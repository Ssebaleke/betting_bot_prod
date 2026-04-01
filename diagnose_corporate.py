from payments.models import Payment
from subscription.models import Subscription
from predictions.models import Prediction
from django.utils import timezone

today = timezone.localtime(timezone.now()).date()
now = timezone.now()

print("=== CORPORATE SUBSCRIBERS ===")
subs = Subscription.objects.filter(
    package__name__icontains="corporate",
    is_active=True
).select_related("user", "package")
print(f"Active: {subs.count()}")
for s in subs:
    latest = Payment.objects.filter(user=s.user, status="SUCCESS").order_by("-created_at").first()
    channel = latest.delivery_channel if latest else "NO PAYMENT"
    phone = latest.phone if latest else "NO PHONE"
    print(f"  user={s.user.username} | pkg={s.package.name} | expires={s.end_date.date()} | channel={channel} | phone={phone}")

print("\n=== CORPORATE PREDICTIONS TODAY ===")
preds = Prediction.objects.filter(
    send_date=today,
    package__name__icontains="corporate"
).select_related("package")
print(f"Count: {preds.count()}")
for p in preds:
    print(f"  {p.home_team} vs {p.away_team} | send_time={p.send_time} | is_sent={p.is_sent} | is_active={p.is_active}")

print("\n=== RECENT CORPORATE PAYMENTS ===")
payments = Payment.objects.filter(
    package__name__icontains="corporate",
    status="SUCCESS"
).select_related("user", "package").order_by("-created_at")[:5]
for p in payments:
    print(f"  {p.phone} | {p.package.name} | {p.created_at.strftime('%Y-%m-%d %H:%M')} | channel={p.delivery_channel} | ref={p.reference[:16]}...")
