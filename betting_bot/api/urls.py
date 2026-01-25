from django.urls import path
from .views import todays_predictions

urlpatterns = [
    path(
        "predictions/today/",
        todays_predictions,
        name="todays_predictions",
    ),
]
