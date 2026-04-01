from payments.services import _build_predictions_message, _deliver_predictions
from predictions.models import Prediction
from subscription.models import Subscription
from payments.models import Payment
from django.utils import timezone

today = timezone.localtime(timezone.now()).date()

# Get corporate predictions - latest sent
latest_date = Prediction.objects.filter(
    is_active=True, is_sent=True,
    package__name__icontains="corporate"
).order_by('-send_date').values_list('send_date', flat=True).first()

preds = list(Prediction.objects.filter(
    is_active=True, is_sent=True,
    send_date=latest_date,
    package__name__icontains="corporate"
).order_by('match_time'))

print(f"Found {len(preds)} corporate predictions for {latest_date}")

# Send to the two subscribers who paid today
phones = ["256742593711", "256740079213"]
for phone in phones:
    user_sub = Subscription.objects.filter(
        user__username=f"web_{phone}",
        is_active=True
    ).select_related("user", "package").first()

    if not user_sub:
        print(f"  No active subscription for {phone}")
        continue

    message = _build_predictions_message(preds, user_sub.package.name, latest_date)
    _deliver_predictions(user_sub.user, phone, "SMS", message)
    print(f"  Sent to {phone} ({user_sub.package.name})")
