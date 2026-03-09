#!/bin/bash

echo "=== Checking Telegram Bot Logs ==="
docker logs bet-bot-telegram-bot --tail=100

echo ""
echo "=== Checking Web Logs ==="
docker logs bet-bot-web --tail=50

echo ""
echo "=== Checking Payment Provider Config ==="
docker exec bet-bot-web python manage.py shell << 'EOF'
from payments.models import PaymentProvider, PaymentProviderConfig

providers = PaymentProvider.objects.all()
print(f"\nProviders: {providers.count()}")
for p in providers:
    print(f"  {p.name}: active={p.is_active}, url={p.base_url}")
    
configs = PaymentProviderConfig.objects.all()
print(f"\nConfigs: {configs.count()}")
for c in configs:
    print(f"  {c.provider.name}: active={c.is_active}")
    print(f"    webhook: {c.webhook_url}")
    
active = PaymentProvider.objects.filter(is_active=True).first()
if active:
    print(f"\n✅ Active: {active.name}")
    if hasattr(active, 'config') and active.config.is_active:
        print("✅ Config active")
    else:
        print("❌ Config NOT active")
else:
    print("\n❌ NO ACTIVE PROVIDER")
EOF
