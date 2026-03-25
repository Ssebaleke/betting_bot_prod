from payments.models import SMSBalance, SMSConfig

print("=== SMSBalance ===")
balance = SMSBalance.get()
print(f"  credits: {balance.credits}")
print(f"  price_per_sms: {balance.price_per_sms}")
print(f"  updated_at: {balance.updated_at}")

print("\n=== SMSConfig ===")
configs = SMSConfig.objects.all()
if configs.exists():
    for c in configs:
        print(f"  api_key: {'SET' if c.api_key else 'NOT SET'} | is_active: {c.is_active}")
else:
    print("  No SMSConfig found!")
