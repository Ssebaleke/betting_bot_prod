from predictions.models import Prediction
from payments.models import SMSBalance
from django.utils import timezone

today = timezone.localtime(timezone.now()).date()

print("=== TODAY'S PREDICTIONS DETAIL ===")
for p in Prediction.objects.filter(send_date=today).order_by("send_time"):
    print(f"  {p.home_team} vs {p.away_team}")
    print(f"    created_at : {timezone.localtime(p.created_at)}")
    print(f"    send_time  : {p.send_time}")
    print(f"    is_sent    : {p.is_sent}")
    print(f"    package    : {p.package.name}")

print("\n=== SMS BALANCE ===")
b = SMSBalance.get()
print(f"  credits: {b.credits}")
print(f"  price_per_sms: {b.price_per_sms}")
