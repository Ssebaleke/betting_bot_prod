#!/bin/bash
# Trigger test payment on VPS

echo "=== Initiating test payment ==="
ssh vico@69.164.245.17 << 'EOF'
cd ~/betting_bot_prod
docker exec bet-bot-web python manage.py shell << 'PYTHON'
from django.contrib.auth.models import User
from packages.models import Package
from payments.services import initiate_payment

user = User.objects.filter(username__startswith='tg_').first()
package = Package.objects.first()

if user and package:
    payment = initiate_payment(user=user, package=package, phone='256751790957')
    print(f'\n✅ Payment initiated!')
    print(f'Reference: {payment.reference}')
    print(f'Amount: {payment.amount}')
    print(f'\n📱 Please approve the USSD prompt on your phone within 60 seconds...')
else:
    print('❌ No user or package found')
PYTHON
EOF

echo ""
echo "Waiting 60 seconds for payment approval and webhook callback..."
sleep 60

echo ""
echo "=== Checking webhook logs ==="
ssh vico@69.164.245.17 "docker logs bet-bot-web --tail=100 2>&1 | grep -i 'makypay\|webhook\|INFO.*payments'"
