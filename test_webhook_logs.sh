#!/bin/bash
# Test webhook and monitor logs

echo "=== Waiting for deployment to complete (30 seconds) ==="
sleep 30

echo ""
echo "=== Triggering test payment ==="
ssh vico@69.164.245.17 "cd ~/betting_bot_prod && docker exec bet-bot-web python manage.py shell -c \"
from django.contrib.auth.models import User
from packages.models import Package
from payments.services import initiate_payment

user = User.objects.filter(username__startswith='tg_').first()
package = Package.objects.first()
if user and package:
    payment = initiate_payment(user=user, package=package, phone='256751790957')
    print(f'Payment initiated: {payment.reference}')
else:
    print('No user or package found')
\""

echo ""
echo "=== Waiting 60 seconds for user to approve payment ==="
echo "Please approve the payment on your phone now..."
sleep 60

echo ""
echo "=== Checking webhook logs ==="
ssh vico@69.164.245.17 "docker logs bet-bot-web --tail=50 | grep -A5 -B5 'MakyPay\|webhook'"
