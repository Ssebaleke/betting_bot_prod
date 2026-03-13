#!/bin/bash
# Setup Nginx reverse proxy with SSL for bet.h2wrestuarantcafe.xyz

DOMAIN="bet.h2wrestuarantcafe.xyz"
EMAIL="your-email@example.com"  # Change this to your email

echo "=== Setting up Nginx + SSL for $DOMAIN ==="

ssh vico@69.164.245.17 << EOF

# Install Nginx and Certbot
echo "1. Installing Nginx and Certbot..."
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# Create Nginx config for betting bot
echo "2. Creating Nginx configuration..."
sudo tee /etc/nginx/sites-available/betting-bot << 'NGINX_CONFIG'
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
NGINX_CONFIG

# Enable the site
echo "3. Enabling site..."
sudo ln -sf /etc/nginx/sites-available/betting-bot /etc/nginx/sites-enabled/

# Test Nginx config
echo "4. Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "5. Restarting Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

# Check if domain resolves
echo "6. Checking if domain resolves..."
if ping -c 2 $DOMAIN > /dev/null 2>&1; then
    echo "✅ Domain resolves! Getting SSL certificate..."
    
    # Get SSL certificate
    sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL
    
    echo ""
    echo "✅ Setup complete!"
    echo "Your betting bot is now available at: https://$DOMAIN"
else
    echo "⚠️  Domain doesn't resolve yet. Please:"
    echo "   1. Add DNS A record in Namecheap (bet -> 69.164.245.17)"
    echo "   2. Wait 5-30 minutes for DNS propagation"
    echo "   3. Run this script again"
fi

EOF

echo ""
echo "=== Next Steps ==="
echo "1. Update webhook URL in database to: https://$DOMAIN/webhook/makypay/"
echo "2. Update MakyPay dashboard with new webhook URL"
