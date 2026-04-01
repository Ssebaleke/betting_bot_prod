from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.http import JsonResponse

from packages.models import Package, PackageCategory
from predictions.models import Prediction
from subscription.models import Subscription
from payments.models import Payment


def is_owner(user):
    return user.is_authenticated and (user.is_staff or user.groups.filter(name="Owner").exists())


def owner_required(view_func):
    return login_required(
        user_passes_test(is_owner, login_url="/dashboard/login/")(view_func),
        login_url="/dashboard/login/"
    )


def login_view(request):
    if request.user.is_authenticated and is_owner(request.user):
        return redirect("dashboard:home")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user and is_owner(user):
            login(request, user)
            return redirect("dashboard:home")
        messages.error(request, "Invalid credentials or insufficient permissions.")
    return render(request, "dashboard/login.html")


def logout_view(request):
    logout(request)
    return redirect("dashboard:login")


@owner_required
def home(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    week_ago = today - timezone.timedelta(days=6)

    success_qs = Payment.objects.filter(status=Payment.STATUS_SUCCESS)

    total_revenue = success_qs.aggregate(t=Sum("amount"))["t"] or 0
    month_revenue = success_qs.filter(created_at__date__gte=month_start).aggregate(t=Sum("amount"))["t"] or 0
    today_revenue = success_qs.filter(created_at__date=today).aggregate(t=Sum("amount"))["t"] or 0
    week_revenue = success_qs.filter(created_at__date__gte=week_ago).aggregate(t=Sum("amount"))["t"] or 0

    active_subs = Subscription.objects.filter(is_active=True).count()
    new_today = Subscription.objects.filter(created_at__date=today).count()
    new_month = Subscription.objects.filter(created_at__date__gte=month_start).count()
    expiring_soon = Subscription.objects.filter(
        is_active=True,
        end_date__date__lte=today + timezone.timedelta(days=3)
    ).count()

    total_payments = success_qs.count()
    pending_payments = Payment.objects.filter(status=Payment.STATUS_PENDING).count()
    failed_payments = Payment.objects.filter(status=Payment.STATUS_FAILED).count()

    daily = (
        success_qs.filter(created_at__date__gte=week_ago)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("day")
    )

    per_package = (
        success_qs.values("package__name")
        .annotate(total=Sum("amount"), count=Count("id"))
        .order_by("-total")
    )

    recent_payments = Payment.objects.select_related("user", "package").order_by("-created_at")[:8]
    predictions_today = Prediction.objects.filter(send_date=today, is_active=True).count()
    predictions_pending = Prediction.objects.filter(send_date__gte=today, is_sent=False, is_active=True).count()

    from payments.models import OwnerWallet
    wallet = OwnerWallet.get()

    context = {
        "total_revenue": total_revenue,
        "month_revenue": month_revenue,
        "today_revenue": today_revenue,
        "week_revenue": week_revenue,
        "active_subs": active_subs,
        "new_today": new_today,
        "new_month": new_month,
        "expiring_soon": expiring_soon,
        "total_payments": total_payments,
        "pending_payments": pending_payments,
        "failed_payments": failed_payments,
        "daily": list(daily),
        "per_package": list(per_package),
        "recent_payments": recent_payments,
        "predictions_today": predictions_today,
        "predictions_pending": predictions_pending,
        "wallet": wallet,
    }
    return render(request, "dashboard/home.html", context)


@owner_required
def packages(request):
    pkgs = Package.objects.select_related("category").order_by("level")
    return render(request, "dashboard/packages.html", {"packages": pkgs})


@owner_required
def package_create(request):
    categories = PackageCategory.objects.filter(is_active=True)
    if request.method == "POST":
        try:
            cat_id = request.POST.get("category") or None
            Package.objects.create(
                name=request.POST["name"],
                description=request.POST.get("description", ""),
                price=request.POST["price"],
                duration_days=request.POST["duration_days"],
                level=request.POST.get("level", 1),
                category_id=cat_id,
                is_active=True,
            )
            messages.success(request, "Package created successfully.")
            return redirect("dashboard:packages")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "dashboard/package_form.html", {"categories": categories, "action": "Create"})


@owner_required
def package_edit(request, pk):
    pkg = get_object_or_404(Package, pk=pk)
    categories = PackageCategory.objects.filter(is_active=True)
    if request.method == "POST":
        try:
            pkg.name = request.POST["name"]
            pkg.description = request.POST.get("description", "")
            pkg.price = request.POST["price"]
            pkg.duration_days = request.POST["duration_days"]
            pkg.level = request.POST.get("level", 1)
            pkg.category_id = request.POST.get("category") or None
            pkg.save()
            messages.success(request, "Package updated.")
            return redirect("dashboard:packages")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "dashboard/package_form.html", {"pkg": pkg, "categories": categories, "action": "Edit"})


@owner_required
def package_toggle(request, pk):
    pkg = get_object_or_404(Package, pk=pk)
    pkg.is_active = not pkg.is_active
    pkg.save()
    return redirect("dashboard:packages")


@owner_required
def predictions(request):
    preds = Prediction.objects.select_related("package").order_by("-send_date", "match_time")
    packages_list = Package.objects.filter(is_active=True)
    return render(request, "dashboard/predictions.html", {"predictions": preds, "packages": packages_list})


@owner_required
def prediction_create(request):
    packages_list = Package.objects.filter(is_active=True)
    if request.method == "POST":
        try:
            Prediction.objects.create(
                home_team=request.POST["home_team"],
                away_team=request.POST["away_team"],
                prediction=request.POST["prediction"],
                odds=request.POST["odds"],
                match_time=request.POST["match_time"],
                match_date=request.POST["match_date"],
                send_date=request.POST["send_date"],
                send_time=request.POST.get("send_time", "08:00"),
                package_id=request.POST["package"],
                is_active=True,
            )
            messages.success(request, "Prediction added.")
            return redirect("dashboard:predictions")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "dashboard/prediction_form.html", {"packages": packages_list, "action": "Add"})


@owner_required
def prediction_edit(request, pk):
    pred = get_object_or_404(Prediction, pk=pk)
    packages_list = Package.objects.filter(is_active=True)
    if request.method == "POST":
        try:
            pred.home_team = request.POST["home_team"]
            pred.away_team = request.POST["away_team"]
            pred.prediction = request.POST["prediction"]
            pred.odds = request.POST["odds"]
            pred.match_time = request.POST["match_time"]
            pred.match_date = request.POST["match_date"]
            pred.send_date = request.POST["send_date"]
            pred.send_time = request.POST.get("send_time", "08:00")
            pred.package_id = request.POST["package"]
            pred.save()
            messages.success(request, "Prediction updated.")
            return redirect("dashboard:predictions")
        except Exception as e:
            messages.error(request, f"Error: {e}")
    return render(request, "dashboard/prediction_form.html", {"pred": pred, "packages": packages_list, "action": "Edit"})


@owner_required
def prediction_delete(request, pk):
    pred = get_object_or_404(Prediction, pk=pk)
    if request.method == "POST":
        pred.delete()
        messages.success(request, "Prediction deleted.")
    return redirect("dashboard:predictions")


@owner_required
def package_delete(request, pk):
    pkg = get_object_or_404(Package, pk=pk)
    if request.method == "POST":
        try:
            pkg.delete()
            messages.success(request, f"Package '{pkg.name}' deleted.")
        except Exception as e:
            messages.error(request, f"Cannot delete: {e}")
    return redirect("dashboard:packages")


@owner_required
def subscriber_add(request):
    packages_list = Package.objects.filter(is_active=True)
    if request.method == "POST":
        phone = (request.POST.get("phone") or "").strip()
        package_id = request.POST.get("package")
        duration_days = request.POST.get("duration_days")
        if not phone or not package_id or not duration_days:
            messages.error(request, "Phone, package and duration are required.")
        else:
            try:
                from payments.makypay import normalize_ug_phone
                from django.contrib.auth.models import User
                normalized = normalize_ug_phone(phone)
                username = f"web_{normalized}"
                user, _ = User.objects.get_or_create(username=username, defaults={"first_name": normalized})
                package = get_object_or_404(Package, pk=package_id)
                start = timezone.now()
                end = start + timezone.timedelta(days=int(duration_days))
                Subscription.objects.create(user=user, package=package, start_date=start, end_date=end, is_active=True)
                messages.success(request, f"Subscriber {normalized} added to {package.name}.")
                return redirect("dashboard:subscribers")
            except Exception as e:
                messages.error(request, f"Error: {e}")
    return render(request, "dashboard/subscriber_add.html", {"packages": packages_list})


@owner_required
def subscriber_delete(request, pk):
    sub = get_object_or_404(Subscription, pk=pk)
    if request.method == "POST":
        sub.delete()
        messages.success(request, "Subscriber removed.")
    return redirect("dashboard:subscribers")


@owner_required
def subscribers(request):
    from django.core.paginator import Paginator
    subs_qs = Subscription.objects.select_related("user", "package").order_by("-created_at")
    paginator = Paginator(subs_qs, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/subscribers.html", {"page_obj": page, "total": subs_qs.count()})


@owner_required
def subscriber_toggle(request, pk):
    sub = get_object_or_404(Subscription, pk=pk)
    if request.method == "POST":
        sub.is_active = not sub.is_active
        sub.save(update_fields=["is_active"])
        action = "activated" if sub.is_active else "suspended"
        messages.success(request, f"Subscription {action} for {sub.user.username}.")
    return redirect("dashboard:subscribers")


@owner_required
def payments(request):
    from django.core.paginator import Paginator
    pmts_qs = Payment.objects.select_related("user", "package").order_by("-created_at")
    paginator = Paginator(pmts_qs, 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/payments.html", {"page_obj": page, "total": pmts_qs.count()})


@owner_required
def manual_send(request):
    import json
    from predictions.models import Prediction
    from payments.sms import send_sms
    from payments.services import _build_predictions_message, _strip_markdown

    packages_list = Package.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        package_id = request.POST.get("package")
        prediction_ids = request.POST.getlist("predictions")
        send_to = request.POST.get("send_to")  # "all" or "custom"
        custom_phones = request.POST.get("custom_phones", "").strip()

        if not package_id or not prediction_ids:
            messages.error(request, "Please select a package and at least one prediction.")
            return redirect("dashboard:manual_send")

        package = get_object_or_404(Package, pk=package_id)
        preds = list(Prediction.objects.filter(
            id__in=prediction_ids, package=package
        ).order_by("match_time"))

        if not preds:
            messages.error(request, "No valid predictions found.")
            return redirect("dashboard:manual_send")

        # Build phone list
        phones = []
        if send_to == "all":
            active_subs = Subscription.objects.filter(
                package=package, is_active=True, end_date__gt=timezone.now()
            ).select_related("user")
            for sub in active_subs:
                latest = Payment.objects.filter(
                    user=sub.user, status=Payment.STATUS_SUCCESS
                ).order_by("-created_at").first()
                if latest and latest.phone:
                    phones.append(latest.phone)
        else:
            for line in custom_phones.splitlines():
                phone = line.strip().replace(" ", "")
                if phone:
                    if phone.startswith("0"):
                        phone = "256" + phone[1:]
                    elif not phone.startswith("256"):
                        phone = "256" + phone
                    phones.append(phone)

        if not phones:
            messages.error(request, "No phone numbers to send to.")
            return redirect("dashboard:manual_send")

        from datetime import date
        send_date = preds[0].send_date if preds else date.today()
        message = _strip_markdown(_build_predictions_message(preds, package.name, send_date))

        sent = 0
        failed = 0
        for phone in set(phones):  # deduplicate
            if send_sms(phone, message):
                sent += 1
            else:
                failed += 1

        if sent:
            messages.success(request, f"✅ Sent to {sent} number(s). {f'❌ {failed} failed.' if failed else ''}")
        else:
            messages.error(request, f"❌ All {failed} sends failed. Check SMS credits.")

        return redirect("dashboard:manual_send")

    return render(request, "dashboard/manual_send.html", {"packages": packages_list})


@owner_required
def manual_send_subscribers(request):
    """AJAX — return active subscribers for a package."""
    package_id = request.GET.get("package_id")
    if not package_id:
        return JsonResponse({"subscribers": []})
    subs = Subscription.objects.filter(
        package_id=package_id, is_active=True, end_date__gt=timezone.now()
    ).select_related("user")
    data = []
    for s in subs:
        latest = Payment.objects.filter(
            user=s.user, status=Payment.STATUS_SUCCESS
        ).order_by("-created_at").first()
        phone = latest.phone if latest else ""
        data.append({"username": s.user.username, "phone": phone})
    return JsonResponse({"subscribers": data})


@owner_required
def manual_send_predictions(request):
    """AJAX — return predictions for a package."""
    package_id = request.GET.get("package_id")
    if not package_id:
        return JsonResponse({"predictions": []})
    from predictions.models import Prediction
    from datetime import timedelta
    from django.utils import timezone
    since = timezone.localtime(timezone.now()).date() - timedelta(days=7)
    preds = Prediction.objects.filter(
        package_id=package_id, is_active=True, send_date__gte=since
    ).order_by("-send_date", "match_time").values(
        "id", "home_team", "away_team", "prediction", "odds", "send_date", "match_time", "is_sent"
    )
    return JsonResponse({"predictions": list(preds)})


@owner_required
def sms_log(request):
    from payments.models import SMSLog
    from django.core.paginator import Paginator

    status_filter = request.GET.get("status", "")
    qs = SMSLog.objects.all()
    if status_filter in ("SENT", "FAILED"):
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "dashboard/sms_log.html", {
        "page_obj": page,
        "status_filter": status_filter,
        "total": qs.count(),
    })


@owner_required
def sms_credits(request):
    from payments.models import SMSBalance, SMSTopUp
    from django.db.models import Sum
    balance = SMSBalance.get()
    topups = SMSTopUp.objects.order_by("-created_at")[:20]
    total_spent = SMSTopUp.objects.filter(status=SMSTopUp.STATUS_SUCCESS).aggregate(t=Sum("amount_paid"))["t"] or 0
    return render(request, "dashboard/sms_credits.html", {
        "balance": balance,
        "topups": topups,
        "total_spent": total_spent,
    })

@owner_required
def sms_topup_pay(request):
    import json, uuid
    from decimal import Decimal
    from payments.models import SMSBalance, SMSTopUp, YooPaymentProvider
    from payments.yoo_client import YooClient, make_reference, normalize_phone as normalize_yoo_phone
    from payments.makypay import normalize_ug_phone

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    phone = (data.get("phone") or "").strip()
    amount = data.get("amount")

    if not phone or not amount:
        return JsonResponse({"success": False, "error": "Phone and amount required"}, status=400)

    balance = SMSBalance.get()
    if not balance.price_per_sms or balance.price_per_sms <= 0:
        return JsonResponse({"success": False, "error": "SMS price not set. Contact developer."}, status=400)

    amount = Decimal(str(amount))
    credits_to_add = int(amount // balance.price_per_sms)
    if credits_to_add < 1:
        return JsonResponse({"success": False, "error": f"Minimum amount is UGX {int(balance.price_per_sms):,} for 1 credit."}, status=400)

    reference = make_reference()

    topup = SMSTopUp.objects.create(
        phone=phone,
        amount_paid=amount,
        credits_added=credits_to_add,
        payment_reference=reference,
        status=SMSTopUp.STATUS_PENDING,
    )

    try:
        provider = YooPaymentProvider.objects.filter(is_active=True).first()
        if not provider:
            topup.delete()
            return JsonResponse({"success": False, "error": "No payment provider configured."}, status=400)

        client = YooClient(api_username=provider.api_username, api_password=provider.api_password)
        result = client.collect(
            phone=normalize_yoo_phone(phone),
            amount=int(amount),
            reference=reference,
            notification_url=provider.notification_url,
            failure_url=provider.failure_url,
        )

        if result.get("yoo_status") == "FAILED":
            topup.status = SMSTopUp.STATUS_FAILED
            topup.save(update_fields=["status"])
            return JsonResponse({"success": False, "error": result.get("error_message") or "Payment rejected."}, status=400)

    except Exception as e:
        topup.status = SMSTopUp.STATUS_FAILED
        topup.save(update_fields=["status"])
        return JsonResponse({"success": False, "error": str(e)}, status=400)

    return JsonResponse({"success": True, "reference": reference, "credits": credits_to_add})


@owner_required
def owner_wallet(request):
    from payments.models import OwnerWallet, WithdrawalRequest, RevenueConfig
    wallet = OwnerWallet.get()
    config = RevenueConfig.get()
    withdrawals = WithdrawalRequest.objects.order_by("-created_at")[:20]
    return render(request, "dashboard/owner_wallet.html", {
        "wallet": wallet,
        "config": config,
        "withdrawals": withdrawals,
    })


@owner_required
def owner_withdraw(request):
    import json
    from decimal import Decimal
    from payments.models import OwnerWallet, WithdrawalRequest, LivePayProvider
    from payments.live_client import LivePayClient

    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    amount = data.get("amount")
    phone = (data.get("phone") or "").strip()
    network = (data.get("network") or "MTN").upper()

    if not amount or not phone:
        return JsonResponse({"success": False, "error": "Amount and phone are required"}, status=400)

    amount = Decimal(str(amount))

    if amount < 10000:
        return JsonResponse({"success": False, "error": "Minimum withdrawal is UGX 10,000"}, status=400)

    wallet = OwnerWallet.get()
    if amount > wallet.balance:
        return JsonResponse({"success": False, "error": "Insufficient wallet balance"}, status=400)

    provider = LivePayProvider.objects.filter(is_active=True).first()
    if not provider:
        return JsonResponse({"success": False, "error": "No active LivePay provider configured"}, status=400)

    if not provider.transaction_pin:
        return JsonResponse({"success": False, "error": "LivePay transaction PIN not configured"}, status=400)

    import uuid as _uuid
    ref = str(_uuid.uuid4()).replace("-", "")

    client = LivePayClient(public_key=provider.public_key, secret_key=provider.secret_key)
    result = client.send(
        amount=int(amount),
        phone=phone,
        network=network,
        pin=provider.transaction_pin,
        reference=ref,
    )

    if result.get("status") != "success":
        error_msg = result.get("message") or "Disbursement failed"
        WithdrawalRequest.objects.create(
            amount=amount,
            payout_phone=phone,
            payout_network=network,
            status=WithdrawalRequest.STATUS_FAILED,
            failure_reason=error_msg,
        )
        return JsonResponse({"success": False, "error": error_msg}, status=400)

    # Deduct wallet and record withdrawal
    from django.db import transaction as db_tx
    with db_tx.atomic():
        locked = OwnerWallet.objects.select_for_update().get(pk=1)
        if amount > locked.balance:
            return JsonResponse({"success": False, "error": "Insufficient balance"}, status=400)
        locked.balance -= amount
        locked.save(update_fields=["balance", "updated_at"])

        WithdrawalRequest.objects.create(
            amount=amount,
            payout_phone=phone,
            payout_network=network,
            status=WithdrawalRequest.STATUS_PAID,
        )

    return JsonResponse({"success": True, "message": f"UGX {int(amount):,} sent to {phone}"})
