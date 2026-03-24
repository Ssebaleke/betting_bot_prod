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
def subscribers(request):
    subs = Subscription.objects.select_related("user", "package").order_by("-created_at")
    return render(request, "dashboard/subscribers.html", {"subscribers": subs})


@owner_required
def payments(request):
    pmts = Payment.objects.select_related("user", "package").order_by("-created_at")
    return render(request, "dashboard/payments.html", {"payments": pmts})


@owner_required
def sms_credits(request):
    from payments.models import SMSConfig
    config = SMSConfig.objects.filter(is_active=True).first()
    return render(request, "dashboard/sms_credits.html", {"config": config})
