from django.urls import path
from .views import index, categories_api

urlpatterns = [
    path("", index, name="landing"),
    path("api/categories/", categories_api, name="landing_categories"),
]
