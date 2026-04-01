from predictions.models import Prediction
from subscription.models import Subscription
from payments.models import Payment
from django.utils import timezone

now = timezone.now()
local_now = timezone.localtime(now)
today = local_now.date()
current_time = local_now.time()

print(f"=== SERVER TIME ===")
print(f"  UTC now:   {now}")
print(f"  Local now: {local_now}")
print(f"  Today:     {today}")
print(f"  Time:      {current_time}")

print(f"\n=== TODAY'S PREDICTIONS ===")
all_today = Prediction.objects.filter(send_date=today).select_related("package")
print(f"  Total for today: {all_today.count()}")
for p in all_today:
    due = p.send_time <= current_time
    print(f"  {'[DUE]' if due else '[NOT DUE]'} {p.home_team} vs {p.away_team} | send_time={p.send_time} | is_sent={p.is_sent} | is_active={p.is_active} | pkg={p.package.name}")

print(f"\n=== UNSENT DUE PREDICTIONS ===")
unsent = Prediction.objects.filter(
    is_active=True,
    is_sent=False,
    send_date=today,
    send_time__lte=current_time,
)
print(f"  Count: {unsent.count()}")

print(f"\n=== ACTIVE SUBSCRIBERS ===")
subs = Subscription.objects.filter(is_active=True, end_date__gt=now).select_related("user", "package")
print(f"  Total: {subs.count()}")
for s in subs:
    latest = Payment.objects.filter(user=s.user, status="SUCCESS").order_by("-created_at").first()
    channel = latest.delivery_channel if latest else "NO PAYMENT"
    print(f"  {s.user.username} | pkg={s.package.name} | channel={channel}")

print(f"\n=== SCHEDULER CRON LOG (last 20 lines) ===")
import subprocess
try:
    result = subprocess.run(
        ["tail", "-20", "/var/log/predictions.log"],
        capture_output=True, text=True
    )
    print(result.stdout or "  Log is empty")
except Exception as e:
    print(f"  Could not read log: {e}")
