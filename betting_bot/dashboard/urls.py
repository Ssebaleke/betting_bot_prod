from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Packages
    path("packages/", views.packages, name="packages"),
    path("packages/create/", views.package_create, name="package_create"),
    path("packages/<int:pk>/edit/", views.package_edit, name="package_edit"),
    path("packages/<int:pk>/toggle/", views.package_toggle, name="package_toggle"),
    path("packages/<int:pk>/delete/", views.package_delete, name="package_delete"),

    # Predictions
    path("predictions/", views.predictions, name="predictions"),
    path("predictions/create/", views.prediction_create, name="prediction_create"),
    path("predictions/<int:pk>/edit/", views.prediction_edit, name="prediction_edit"),
    path("predictions/<int:pk>/delete/", views.prediction_delete, name="prediction_delete"),

    # Subscribers & Payments
    path("subscribers/", views.subscribers, name="subscribers"),
    path("subscribers/add/", views.subscriber_add, name="subscriber_add"),
    path("subscribers/<int:pk>/toggle/", views.subscriber_toggle, name="subscriber_toggle"),
    path("subscribers/<int:pk>/delete/", views.subscriber_delete, name="subscriber_delete"),
    path("payments/", views.payments, name="payments"),

    # SMS Credits
    path("sms-credits/", views.sms_credits, name="sms_credits"),
    path("sms-credits/pay/", views.sms_topup_pay, name="sms_topup_pay"),
    path("sms-log/", views.sms_log, name="sms_log"),
]
