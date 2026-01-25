from django.contrib import admin
from .models import Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "duration_days",
        "level",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "level",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "level",
        "price",
    )
