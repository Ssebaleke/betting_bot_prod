# Webhook Debugging Steps

## Changes Made
1. Added detailed logging to `makypay_webhook` view to capture:
   - Raw request body and content type
   - Parsed JSON payload
   - Missing fields warnings
   
2. Added Django logging configuration to output to console

## Next Steps

### 1. Wait for deployment (GitHub Actions takes ~2 minutes)
Check: https://github.com/Ssebaleke/betting_bot_prod/actions

### 2. SSH into VPS and restart containers
```bash
ssh vico@69.164.245.17
cd ~/betting_bot_prod
git pull
docker-compose down
docker-compose up -d
docker logs -f bet-bot-web
```

### 3. Trigger a test payment via Telegram bot
Send `/subscribe` command to your bot

### 4. Approve the USSD prompt on your phone

### 5. Check logs for webhook callback
```bash
docker logs bet-bot-web --tail=100 | grep -i "makypay"
```

## What to Look For

The logs should now show:
- `MakyPay webhook received: body=...` - Shows what MakyPay sent
- `MakyPay webhook payload: {...}` - Shows parsed JSON
- `Missing fields in webhook: ...` - If fields are missing

This will tell us exactly what MakyPay is sending and why it's returning "Bad Request".

## Common Issues

1. **MakyPay sends form data instead of JSON** - We'll see this in content_type
2. **Field names don't match** - We'll see the actual field names in payload
3. **Status value is different** - We'll see what status value they use
