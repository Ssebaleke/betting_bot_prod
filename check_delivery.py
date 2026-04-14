from django.utils import timezone
local_now = timezone.localtime(timezone.now())
today = local_now.date()

print(f"Today: {today}")

try:
    from predictions.models import PredictionDelivery
    records = PredictionDelivery.objects.filter(send_date=today).select_related("user", "package")
    print(f"PredictionDelivery records today: {records.count()}")
    for r in records[:10]:
        print(f"  {r.user.username} | {r.package.name} | {r.send_date}")
except Exception as e:
    print(f"Error: {e}")

from predictions.models import Prediction
preds = Prediction.objects.filter(send_date=today, is_active=True)
print(f"\nPredictions for today: {preds.count()}")
for p in preds:
    print(f"  {p.home_team} vs {p.away_team} | is_sent={p.is_sent} | send_time={p.send_time} | pkg={p.package.name}")
