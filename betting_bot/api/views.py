from datetime import timedelta
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from predictions.models import Prediction


@login_required
def todays_predictions(request):
    user = request.user

    # ✅ FIX: get ACTIVE subscription correctly
    subscription = user.subscriptions.filter(is_active=True).first()

    if not subscription:
        return JsonResponse(
            {"detail": "No active subscription"},
            status=403,
        )

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
        package=subscription.package,  # ✅ exact package
    ).select_related(
        "fixture",
        "market",
        "package",
    ).order_by("publish_at")

    data = []

    for p in predictions:
        data.append({
            "fixture": {
                "home_team": p.fixture.home_team,
                "away_team": p.fixture.away_team,
                "start_time": p.fixture.start_time,
            },
            "market": p.market.name,
            "selection": p.selection,
            "odds": str(p.odds_value),
            "package": p.package.name,
            "publish_at": p.publish_at,
        })

    return JsonResponse(
        {
            "date": start_of_day.date(),
            "count": len(data),
            "predictions": data,
        }
    )
