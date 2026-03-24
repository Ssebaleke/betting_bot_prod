from django.urls import path
from django.http import HttpResponse
from .views import (
    initiate_payment_view,
    makypay_webhook,
    payment_status,
    initiate_yoo_payment_view,
    yoo_ipn,
    yoo_failure_ipn,
)

def home(request):
    return HttpResponse("Betting bot API is running ✅")

urlpatterns = [
    path("", home),
    path("initiate/", initiate_payment_view, name="initiate_payment"),
    path("initiate/yoo/", initiate_yoo_payment_view, name="initiate_yoo_payment"),
    path("webhook/makypay/", makypay_webhook, name="makypay_webhook"),
    path("webhook/yoo/ipn/", yoo_ipn, name="yoo_ipn"),
    path("webhook/yoo/failure/", yoo_failure_ipn, name="yoo_failure_ipn"),
    path("status/<str:reference>/", payment_status, name="payment_status"),
]
