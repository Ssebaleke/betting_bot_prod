import json
import logging

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from packages.models import PackageCategory

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "landing/index.html")


@require_GET
def categories_api(request):
    """Return active categories with their active packages as JSON."""
    categories = PackageCategory.objects.filter(is_active=True).prefetch_related("packages")
    data = []
    for cat in categories:
        packages = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": str(p.price),
                "duration_days": p.duration_days,
            }
            for p in cat.packages.filter(is_active=True).order_by("level")
        ]
        if packages:
            data.append({"id": cat.id, "name": cat.name, "description": cat.description, "packages": packages})
    return JsonResponse({"categories": data})
