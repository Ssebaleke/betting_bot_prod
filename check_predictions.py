from predictions.models import Prediction
from subscription.models import Subscription
from django.utils import timezone

today = timezone.localtime(timezone.now()).date()
now_time = timezone.localtime(timezone.now()).time()

print("=== SERVER TIME ===")
print("Today (EAT):", today)
print("Now (EAT):", now_time)

print("\n=== PREDICTIONS FOR TODAY ===")
preds = list(Prediction.objects.filter(send_date=today).select_related("package").order_by("send_time"))
print("Total:", len(preds))
for p in preds:
    due = "DUE" if p.send_time <= now_time else "PENDING"
    print(f"  [{due}] {p.home_team} vs {p.away_team} | send_time={p.send_time} | is_sent={p.is_sent} | is_active={p.is_active} | pkg={p.package.name}")

print("\n=== UNSENT DUE PREDICTIONS ===")
unsent = [p for p in preds if not p.is_sent and p.is_active and p.send_time <= now_time]
print("Count:", len(unsent))

print("\n=== ACTIVE SUBSCRIPTIONS ===")
subs = list(Subscription.objects.filter(is_active=True, end_date__gt=timezone.now()).select_related("user", "package"))
print("Total active subscribers:", len(subs))
for s in subs:
    print(f"  {s.user.username} | pkg={s.package.name} | expires={s.end_date.date()}")
