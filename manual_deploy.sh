#!/bin/bash
# Manual deployment script

echo "=== Checking current deployment status ==="
ssh vico@69.164.245.17 << 'EOF'
cd ~/betting_bot_prod
echo "Current commit:"
git log --oneline -1

echo ""
echo "Checking if logging code exists:"
grep -c "logger.info" betting_bot/payments/views.py || echo "Logging code NOT found"

echo ""
echo "=== Pulling latest code ==="
git fetch origin
git reset --hard origin/main

echo ""
echo "Verifying logging code after pull:"
grep -c "logger.info" betting_bot/payments/views.py

echo ""
echo "=== Restarting containers ==="
docker-compose down
docker-compose up -d

echo ""
echo "=== Waiting for containers to start ==="
sleep 10

echo ""
echo "=== Container status ==="
docker-compose ps
EOF

echo ""
echo "✅ Deployment complete. Now trigger a test payment."
