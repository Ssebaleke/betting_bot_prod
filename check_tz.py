from predictions.models import Prediction
from django.utils import timezone
import subprocess

today = timezone.localtime(timezone.now()).date()

print("=== SCHEDULER TIMEZONE CHECK ===")
import time
print(f"  System TZ: {time.tzname}")
print(f"  Django localtime: {timezone.localtime(timezone.now())}")
print(f"  Django now (UTC): {timezone.now()}")

print("\n=== ALL PREDICTIONS THIS WEEK ===")
from datetime import timedelta
week_ago = today - timedelta(days=3)
for p in Prediction.objects.filter(send_date__gte=week_ago).order_by("-send_date", "send_time"):
    print(f"  {p.send_date} {p.send_time} | {p.home_team} vs {p.away_team} | is_sent={p.is_sent} | pkg={p.package.name} | created={timezone.localtime(p.created_at).strftime('%Y-%m-%d %H:%M')}")
