from predictions.models import Prediction
from django.utils import timezone

local_now = timezone.localtime(timezone.now())
today = local_now.date()
current_time = local_now.time()

print(f"Today: {today} | Current time: {current_time}")

print("\n=== ALL PREDICTIONS FOR TODAY ===")
all_preds = Prediction.objects.filter(send_date=today).order_by("send_time")
print(f"Total: {all_preds.count()}")
for p in all_preds:
    due = p.send_time <= current_time
    print(f"  {'[DUE]' if due else '[NOT DUE]'} {p.home_team} vs {p.away_team} | send_time={p.send_time} | is_sent={p.is_sent} | is_active={p.is_active} | pkg={p.package.name}")

print("\n=== UNSENT DUE (what scheduler looks for) ===")
unsent = Prediction.objects.filter(
    is_active=True,
    is_sent=False,
    send_date=today,
    send_time__lte=current_time,
)
print(f"Count: {unsent.count()}")

print("\n=== ALL PREDICTIONS (any date, is_sent=False) ===")
all_unsent = Prediction.objects.filter(is_sent=False, is_active=True).order_by("send_date")
for p in all_unsent:
    print(f"  send_date={p.send_date} | send_time={p.send_time} | {p.home_team} vs {p.away_team} | pkg={p.package.name}")
