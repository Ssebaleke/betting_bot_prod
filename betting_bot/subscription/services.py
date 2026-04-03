from django.utils import timezone
from datetime import timedelta
from .models import Subscription


def create_subscription(user, package):
    start_date = timezone.now()
    end_date = start_date + timedelta(days=package.duration_days)

    # If active subscription for same package exists, extend it
    existing = Subscription.objects.filter(
        user=user,
        package=package,
        is_active=True,
        end_date__gt=timezone.now()
    ).first()

    if existing:
        existing.end_date = existing.end_date + timedelta(days=package.duration_days)
        existing.save(update_fields=["end_date"])
        return existing

    # Otherwise create a new subscription (stacking allowed)
    return Subscription.objects.create(
        user=user,
        package=package,
        start_date=start_date,
        end_date=end_date,
        is_active=True
    )
