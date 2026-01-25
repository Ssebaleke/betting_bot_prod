from .models import Subscription
from django.utils import timezone


def user_has_active_subscription(user, package=None):
    qs = Subscription.objects.filter(
        user=user,
        is_active=True,
        end_date__gt=timezone.now()
    )

    if package:
        qs = qs.filter(package=package)

    return qs.exists()
