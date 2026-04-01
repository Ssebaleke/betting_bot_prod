from predictions.models import Prediction
from django.utils import timezone

today = timezone.localtime(timezone.now()).date()
updated = Prediction.objects.filter(send_date=today, is_sent=True).update(is_sent=False)
print(f"Reset {updated} prediction(s) to is_sent=False for {today}")
print("Scheduler will resend them on the next 15-minute run.")
