#!/bin/bash
# Update ALLOWED_HOSTS to include subdomain

echo "=== Updating ALLOWED_HOSTS on VPS ==="

ssh vico@69.164.245.17 << 'EOF'
cd ~/betting_bot_prod

# Backup current .env
cp .env .env.backup

# Update ALLOWED_HOSTS to include subdomain
sed -i 's/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=69.164.245.17,localhost,127.0.0.1,bet.h2wrestuarantcafe.xyz/' .env

echo "Updated .env file:"
grep ALLOWED_HOSTS .env

echo ""
echo "Restarting web container..."
docker-compose restart web

echo ""
echo "Waiting for container to start..."
sleep 5

echo ""
echo "Testing subdomain..."
curl -I http://localhost:8000 2>&1 | head -5

EOF

echo ""
echo "✅ ALLOWED_HOSTS updated!"
echo "Now you can proceed with Nginx + SSL setup"
