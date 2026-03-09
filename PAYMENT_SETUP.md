# USSD Payment Setup Guide

## Problem: USSD Push Not Working

### Root Causes Found:
1. **Wrong function signature** - `initiate_payment()` was called with `telegram_id` instead of `user` object ✅ FIXED
2. **Missing User creation** - TelegramProfile might not have linked User ✅ FIXED
3. **Payment provider not configured** - Need to verify in Django admin

---

## Setup Steps

### 1. Run Diagnostics
```bash
cd betting_bot
python manage.py shell < test_payment.py
```

This will show:
- Active payment providers
- Configuration status
- Available packages

### 2. Configure Payment Provider in Django Admin

Access: http://127.0.0.1:8000/admin/

#### Create PaymentProvider:
- Name: `MakyPay`
- Base URL: `https://api.makypay.com` (or your MakyPay URL)
- Is Active: ✅ **CHECK THIS**

#### Create PaymentProviderConfig:
- Provider: Select `MakyPay`
- Public Key: (from MakyPay dashboard)
- Secret Key: (from MakyPay dashboard)
- Webhook URL: `https://YOUR_PUBLIC_DOMAIN.com/webhook/makypay/`
  - ⚠️ Must be HTTPS and publicly accessible
  - ⚠️ MakyPay cannot reach localhost/127.0.0.1
- Is Active: ✅ **CHECK THIS**

### 3. Create Test Package

In Django Admin → Packages:
- Name: `Test Package`
- Price: `1000`
- Duration Days: `7`
- Level: `1`
- Is Active: ✅

### 4. Test Payment Flow

1. Start bot: `/start`
2. Select package
3. Enter phone: `0708826558`
4. Check logs for MakyPay request details

---

## Common Issues

### Issue: "No active payment provider configured"
**Fix:** Go to admin → PaymentProvider → Set `is_active=True`

### Issue: "Active provider has no active config"
**Fix:** Go to admin → PaymentProviderConfig → Set `is_active=True`

### Issue: MakyPay returns 401 Unauthorized
**Fix:** Verify `secret_key` in PaymentProviderConfig

### Issue: MakyPay returns 400 Bad Request
**Fix:** Check phone number format (should be 2567XXXXXXXX)

### Issue: USSD push sent but user doesn't receive
**Possible causes:**
- Phone number incorrect
- Network provider issue (MTN/Airtel)
- MakyPay account not funded
- Phone not registered for mobile money

---

## Logs to Check

### Telegram Bot Container:
```bash
docker logs bet-bot-telegram-bot -f
```

Look for:
- `MakyPay START ref=...`
- `=== MakyPay Request ===`
- Response status and body

### Web Container:
```bash
docker logs bet-bot-web -f
```

Look for webhook callbacks from MakyPay

---

## Next Steps After Payment Works

1. **Add subscription creation** - Currently payment succeeds but subscription isn't created
2. **Add payment status polling** - Let users check payment status
3. **Add payment timeout handling** - Cancel after 5 minutes
4. **Add retry mechanism** - If MakyPay API fails
