from datetime import timedelta
from django.utils import timezone

from predictions.models import Prediction


def get_todays_predictions_for_user(user):
    subscription = user.subscriptions.filter(is_active=True).first()

    if not subscription:
        return None, []

    now = timezone.now()

    start_of_day = now.replace( 
        hour=0, minute=0, second=0, microsecond=0
    )
    end_of_day = start_of_day + timedelta(days=1)

    predictions = Prediction.objects.filter(
        is_active=True,
        publish_at__gte=start_of_day,
        publish_at__lt=end_of_day,
        publish_at__lte=now,
        package=subscription.package,
    ).select_related(
        "fixture",
        "market",
        "package",
    ).order_by("publish_at")

    return subscription, list(predictions)
