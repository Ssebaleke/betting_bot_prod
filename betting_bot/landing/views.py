import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from packages.models import Package

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "landing/index.html")


@require_GET
def packages_api(request):
    """Return all active packages as JSON."""
    packages = Package.objects.filter(is_active=True).order_by("level")
    data = [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": str(p.price),
            "duration_days": p.duration_days,
        }
        for p in packages
    ]
    return JsonResponse({"packages": data})
