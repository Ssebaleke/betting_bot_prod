from django.contrib import admin
from .models import Package, PackageCategory


@admin.register(PackageCategory)
class PackageCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active", "package_count")
    list_editable = ("order", "is_active")
    search_fields = ("name",)

    def package_count(self, obj):
        return obj.packages.count()
    package_count.short_description = "Packages"


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "duration_days",
        "level",
        "is_active",
    )
    list_filter = ("is_active", "category", "level")
    search_fields = ("name", "description")
    ordering = ("category", "level", "price")
    list_select_related = ("category",)
