# Setup Subdomain with Nginx + SSL

## Prerequisites
1. ✅ Domain: h2wrestuarantcafe.xyz
2. ✅ VPS IP: 69.164.245.17
3. ✅ Subdomain: bet.h2wrestuarantcafe.xyz
4. ⏳ DNS A Record: Add in Namecheap (bet -> 69.164.245.17)

## Step 1: Add DNS Record in Namecheap

Go to Namecheap → h2wrestuarantcafe.xyz → Advanced DNS → Add Record:
```
Type: A Record
Host: bet
Value: 69.164.245.17
TTL: Automatic
```

## Step 2: Wait for DNS Propagation (5-30 minutes)

Test with:
```bash
ping bet.h2wrestuarantcafe.xyz
```

## Step 3: Install Nginx on VPS

```bash
ssh vico@69.164.245.17
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx
```

## Step 4: Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/betting-bot
```

Paste this:
```nginx
server {
    listen 80;
    server_name bet.h2wrestuarantcafe.xyz;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
```

Save: `Ctrl+X`, `Y`, `Enter`

## Step 5: Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/betting-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Step 6: Get SSL Certificate (HTTPS)

```bash
sudo certbot --nginx -d bet.h2wrestuarantcafe.xyz --non-interactive --agree-tos -m your-email@example.com
```

Replace `your-email@example.com` with your actual email.

## Step 7: Test

```bash
curl https://bet.h2wrestuarantcafe.xyz
```

Should return: "Betting bot API is running ✅"

## Step 8: Update Webhook URL in Database

```bash
cd ~/betting_bot_prod
docker exec bet-bot-web python manage.py shell
```

In the shell:
```python
from payments.models import PaymentProviderConfig
config = PaymentProviderConfig.objects.first()
config.webhook_url = 'https://bet.h2wrestuarantcafe.xyz/webhook/makypay/'
config.save()
print(f"✅ Webhook URL updated to: {config.webhook_url}")
exit()
```

## Step 9: Update MakyPay Dashboard

Log in to MakyPay dashboard and update webhook URL to:
```
https://bet.h2wrestuarantcafe.xyz/webhook/makypay/
```

## Step 10: Test Payment

Trigger a test payment and check if webhook is received with HTTPS!

---

## Troubleshooting

**If Nginx fails to start:**
```bash
sudo systemctl status nginx
sudo nginx -t
```

**If SSL fails:**
- Make sure DNS is propagated: `ping bet.h2wrestuarantcafe.xyz`
- Check port 80 is open: `sudo ufw allow 80`
- Check port 443 is open: `sudo ufw allow 443`

**Check Nginx logs:**
```bash
sudo tail -f /var/log/nginx/error.log
```
