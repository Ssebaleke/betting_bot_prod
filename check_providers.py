from payments.models import LivePayProvider, YooPaymentProvider

print("=== LivePay Providers ===")
for p in LivePayProvider.objects.all():
    print(f"  id={p.id} | name={p.name} | is_active={p.is_active} | public_key={'SET' if p.public_key else 'EMPTY'} | secret_key={'SET' if p.secret_key else 'EMPTY'}")

print("\n=== Yoo Providers ===")
for p in YooPaymentProvider.objects.all():
    print(f"  id={p.id} | name={p.name} | is_active={p.is_active}")
