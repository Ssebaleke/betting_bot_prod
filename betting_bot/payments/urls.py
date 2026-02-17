from django.urls import path
from django.http import HttpResponse
from .views import (
    initiate_payment_view,
    makypay_webhook,
    payment_status,
)

def home(request):
    return HttpResponse("Betting bot API is running ✅")

urlpatterns = [
    path("", home),  # <-- this fixes your 404 on /
    path("initiate/", initiate_payment_view, name="initiate_payment"),
    path("webhook/makypay/", makypay_webhook, name="makypay_webhook"),
    path("status/<str:reference>/", payment_status, name="payment_status"),
]

