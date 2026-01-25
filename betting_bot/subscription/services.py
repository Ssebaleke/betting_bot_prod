from django.utils import timezone
from datetime import timedelta
from .models import Subscription


def create_subscription(user, package):
    # Deactivate any existing active subscriptions
    Subscription.objects.filter(
        user=user,
        is_active=True
    ).update(is_active=False)

    start_date = timezone.now()
    end_date = start_date + timedelta(days=package.duration_days)

    return Subscription.objects.create(
        user=user,
        package=package,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
