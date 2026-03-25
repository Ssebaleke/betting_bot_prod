from payments.models import SMSTopUp, SMSBalance

print("=== PENDING TOPUPS ===")
pending = SMSTopUp.objects.filter(status=SMSTopUp.STATUS_PENDING)
print(f"Found: {pending.count()}")
for t in pending:
    print(f"  ref={t.payment_reference} | amount={t.amount_paid} | credits={t.credits_added} | phone={t.phone}")

# Manually confirm the topup since IPN was missed
for t in pending:
    t.status = SMSTopUp.STATUS_SUCCESS
    t.save(update_fields=["status"])
    balance = SMSBalance.get()
    balance.credits += t.credits_added
    balance.save(update_fields=["credits", "updated_at"])
    print(f"  ✅ Confirmed topup: +{t.credits_added} credits")

print(f"\n=== FINAL BALANCE ===")
print(f"  credits: {SMSBalance.get().credits}")
