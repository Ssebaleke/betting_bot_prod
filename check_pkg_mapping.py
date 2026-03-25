from predictions.models import Prediction
from subscription.models import Subscription
from packages.models import Package
from django.utils import timezone

print("=== PACKAGES ===")
for pkg in Package.objects.all():
    print(f"  [{pkg.id}] {pkg.name} | active={pkg.is_active}")

print("\n=== PREDICTIONS (last 5 days) ===")
from datetime import timedelta
since = timezone.localtime(timezone.now()).date() - timedelta(days=5)
preds = Prediction.objects.filter(send_date__gte=since).select_related("package").order_by("-send_date", "send_time")
print("Total:", preds.count())
for p in preds:
    print(f"  {p.send_date} {p.send_time} | {p.home_team} vs {p.away_team} | pkg={p.package.name} | is_sent={p.is_sent}")

print("\n=== SUBSCRIBER -> PACKAGE MAPPING ===")
subs = Subscription.objects.filter(is_active=True, end_date__gt=timezone.now()).select_related("user", "package")
for s in subs:
    print(f"  {s.user.username} -> subscribed to: {s.package.name}")
