from payments.models import Payment
from payments.services import confirm_payment
from django.utils import timezone

print("=== PENDING PAYMENTS ===")
pending = Payment.objects.filter(status=Payment.STATUS_PENDING).select_related("user", "package").order_by("-created_at")
print(f"Found: {pending.count()}")
for p in pending:
    age = timezone.now() - p.created_at
    print(f"  ref={p.reference} | phone={p.phone} | pkg={p.package.name} | amount={p.amount} | age={int(age.total_seconds()//60)}min | channel={p.delivery_channel}")
