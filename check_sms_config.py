from payments.models import SMSConfig, SMSBalance

print("=== SMS CONFIG ===")
configs = SMSConfig.objects.all()
print(f"Total configs: {configs.count()}")
for c in configs:
    print(f"  id={c.id} | api_key={'SET' if c.api_key else 'EMPTY'} | is_active={c.is_active}")

print("\n=== SMS BALANCE ===")
b = SMSBalance.get()
print(f"  credits={b.credits} | price_per_sms={b.price_per_sms}")
