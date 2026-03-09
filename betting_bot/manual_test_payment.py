"""
Manual payment test - Run this to test payment flow directly
Usage: docker exec -it bet-bot-web python manage.py shell < manual_test_payment.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betting_bot.settings')
django.setup()

from django.contrib.auth.models import User
from packages.models import Package
from payments.services import initiate_payment
from payments.models import PaymentProvider, PaymentProviderConfig

print("\n" + "="*50)
print("MANUAL PAYMENT TEST")
print("="*50)

# Check provider
print("\n1. Checking Payment Provider...")
provider = PaymentProvider.objects.filter(is_active=True).first()
if not provider:
    print("❌ NO ACTIVE PROVIDER - Go to admin and activate one!")
    exit(1)

print(f"✅ Provider: {provider.name}")
print(f"   Base URL: {provider.base_url}")

# Check config
if not hasattr(provider, 'config') or not provider.config.is_active:
    print("❌ NO ACTIVE CONFIG - Go to admin and activate config!")
    exit(1)

config = provider.config
print(f"✅ Config active")
print(f"   Webhook: {config.webhook_url}")
print(f"   Secret: {config.secret_key[:10]}...")

# Check package
print("\n2. Checking Packages...")
package = Package.objects.filter(is_active=True).first()
if not package:
    print("❌ NO ACTIVE PACKAGE - Create one in admin!")
    exit(1)

print(f"✅ Package: {package.name} - UGX {package.price}")

# Get or create test user
print("\n3. Getting Test User...")
user, created = User.objects.get_or_create(
    username="test_user",
    defaults={"first_name": "Test", "last_name": "User"}
)
print(f"✅ User: {user.username} (ID: {user.id})")

# Test payment
print("\n4. Testing Payment...")
print("   Phone: 0708826558")
print("   Amount: UGX", package.price)

try:
    payment = initiate_payment(
        user=user,
        package=package,
        phone="0708826558"
    )
    print(f"\n✅ PAYMENT INITIATED!")
    print(f"   Reference: {payment.reference}")
    print(f"   Status: {payment.status}")
    print(f"   Amount: UGX {payment.amount}")
    print("\n📱 Check phone 0708826558 for USSD prompt!")
    
except Exception as e:
    print(f"\n❌ PAYMENT FAILED!")
    print(f"   Error: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "="*50)
