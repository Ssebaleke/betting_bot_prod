"""
Diagnostic script to test payment flow
Run: python manage.py shell < test_payment.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betting_bot.settings')
django.setup()

from payments.models import PaymentProvider, PaymentProviderConfig
from packages.models import Package
from django.contrib.auth.models import User

print("\n=== PAYMENT DIAGNOSTICS ===\n")

# Check PaymentProvider
providers = PaymentProvider.objects.all()
print(f"Total Providers: {providers.count()}")
for p in providers:
    print(f"  - {p.name}: active={p.is_active}, base_url={p.base_url}")

# Check PaymentProviderConfig
configs = PaymentProviderConfig.objects.all()
print(f"\nTotal Configs: {configs.count()}")
for c in configs:
    print(f"  - {c.provider.name}: active={c.is_active}")
    print(f"    webhook_url: {c.webhook_url}")
    print(f"    secret_key: {'*' * 10}{c.secret_key[-4:] if len(c.secret_key) > 4 else '****'}")

# Check active provider
active_provider = PaymentProvider.objects.filter(is_active=True).first()
if active_provider:
    print(f"\n✅ Active Provider: {active_provider.name}")
    config = getattr(active_provider, 'config', None)
    if config and config.is_active:
        print(f"✅ Active Config Found")
    else:
        print(f"❌ NO ACTIVE CONFIG")
else:
    print("\n❌ NO ACTIVE PROVIDER")

# Check packages
packages = Package.objects.filter(is_active=True)
print(f"\nActive Packages: {packages.count()}")
for pkg in packages:
    print(f"  - {pkg.name}: UGX {pkg.price} ({pkg.duration_days} days)")

# Check users
users = User.objects.all()
print(f"\nTotal Users: {users.count()}")

print("\n=== END DIAGNOSTICS ===\n")
