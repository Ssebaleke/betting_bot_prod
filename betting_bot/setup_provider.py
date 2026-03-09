"""
Quick setup script for payment provider
Run: python manage.py shell < setup_provider.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betting_bot.settings')
django.setup()

from payments.models import PaymentProvider, PaymentProviderConfig

# Create or update provider
provider, created = PaymentProvider.objects.get_or_create(
    name="MakyPay",
    defaults={
        "base_url": "https://api.makypay.com",  # UPDATE THIS
        "is_active": True,
    }
)

if not created:
    provider.is_active = True
    provider.save()
    print(f"✅ Updated existing provider: {provider.name}")
else:
    print(f"✅ Created new provider: {provider.name}")

# Create or update config
config, created = PaymentProviderConfig.objects.get_or_create(
    provider=provider,
    defaults={
        "public_key": "YOUR_PUBLIC_KEY",  # UPDATE THIS
        "secret_key": "YOUR_SECRET_KEY",  # UPDATE THIS
        "webhook_url": "https://YOUR_DOMAIN.com/webhook/makypay/",  # UPDATE THIS
        "is_active": True,
    }
)

if not created:
    config.is_active = True
    config.save()
    print(f"✅ Updated existing config")
else:
    print(f"✅ Created new config")

print("\n⚠️  IMPORTANT: Update the following in Django Admin:")
print(f"   - Secret Key: {config.secret_key}")
print(f"   - Public Key: {config.public_key}")
print(f"   - Webhook URL: {config.webhook_url}")
print(f"   - Base URL: {provider.base_url}")
