from django.urls import path
from .views import index, packages_api

urlpatterns = [
    path("", index, name="landing"),
    path("packages/", packages_api, name="landing_packages"),
]
