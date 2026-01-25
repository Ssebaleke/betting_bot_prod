from django.urls import path
from .views import (
    initiate_payment_view,
    makypay_webhook,
    payment_status,
)

urlpatterns = [
    path("initiate/", initiate_payment_view, name="initiate_payment"),
    path("webhook/makypay/", makypay_webhook, name="makypay_webhook"),
    path("status/<str:reference>/", payment_status, name="payment_status"),
]
