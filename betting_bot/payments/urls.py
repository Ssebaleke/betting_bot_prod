from django.urls import path
from django.http import HttpResponse
from .views import (
    initiate_payment_view,
    makypay_webhook,
    payment_status,
    initiate_yoo_payment_view,
    yoo_ipn,
    yoo_failure_ipn,
    landing_initiate_payment,
    initiate_live_payment_view,
    live_ipn,
    kwa_ipn,
)

def home(request):
    return HttpResponse("Betting bot API is running ✅")

urlpatterns = [
    path("", home),
    path("initiate/", initiate_payment_view, name="initiate_payment"),
    path("initiate/yoo/", initiate_yoo_payment_view, name="initiate_yoo_payment"),
    path("initiate/live/", initiate_live_payment_view, name="initiate_live_payment"),
    path("initiate/web/", landing_initiate_payment, name="landing_initiate_payment"),
    path("webhook/makypay/", makypay_webhook, name="makypay_webhook"),
    path("webhook/yoo/ipn/", yoo_ipn, name="yoo_ipn"),
    path("webhook/yoo/failure/", yoo_failure_ipn, name="yoo_failure_ipn"),
    path("webhook/live/ipn/", live_ipn, name="live_ipn"),
    path("webhook/kwa/ipn/", kwa_ipn, name="kwa_ipn"),
    path("status/<str:reference>/", payment_status, name="payment_status"),
]
