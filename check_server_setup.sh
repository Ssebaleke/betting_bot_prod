#!/bin/bash
# Check server setup and configure Nginx with SSL

echo "=== Checking current server setup ==="
ssh vico@69.164.245.17 << 'EOF'

echo "1. Checking if Nginx is installed:"
which nginx || echo "Nginx NOT installed"

echo ""
echo "2. Checking if Certbot is installed:"
which certbot || echo "Certbot NOT installed"

echo ""
echo "3. Checking what's listening on port 80:"
sudo netstat -tlnp | grep :80 || echo "Nothing on port 80"

echo ""
echo "4. Checking what's listening on port 443:"
sudo netstat -tlnp | grep :443 || echo "Nothing on port 443"

echo ""
echo "5. Checking Docker containers:"
docker ps --format "table {{.Names}}\t{{.Ports}}"

echo ""
echo "6. Testing if subdomain resolves:"
ping -c 2 bet.h2wrestuarantcafe.xyz || echo "Subdomain not resolving yet"

EOF
