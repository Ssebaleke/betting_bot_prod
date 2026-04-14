from predictions.models import Prediction
from django.utils import timezone

today = timezone.localtime(timezone.now()).date()

# Reset any unsent predictions for today that are still False
unsent = Prediction.objects.filter(send_date=today, is_sent=False, is_active=True)
print(f"Unsent predictions for today: {unsent.count()}")
for p in unsent:
    print(f"  {p.home_team} vs {p.away_team} | {p.package.name} | send_time={p.send_time}")
print("Scheduler will pick these up on next run.")
