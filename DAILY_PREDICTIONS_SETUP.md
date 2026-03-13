# Automated Daily Predictions Setup

## How It Works

1. **Admin schedules predictions** in Django admin with `publish_at` date/time
2. **Cron job runs daily** at specified time (e.g., 8:00 AM)
3. **System sends predictions** to all active subscribers based on their package
4. **Users receive predictions** via Telegram automatically

## Setup on VPS

### 1. Copy the script to VPS
```bash
scp send_predictions.sh vico@69.164.245.17:~/betting_bot_prod/
ssh vico@69.164.245.17
cd ~/betting_bot_prod
chmod +x send_predictions.sh
```

### 2. Update the script path
```bash
nano send_predictions.sh
```
Change to:
```bash
#!/bin/bash
cd ~/betting_bot_prod
docker exec bet-bot-web python manage.py send_daily_predictions >> ~/predictions_broadcast.log 2>&1
```

### 3. Setup cron job
```bash
crontab -e
```

Add this line to send predictions daily at 8:00 AM:
```
0 8 * * * ~/betting_bot_prod/send_predictions.sh
```

Or for 9:00 AM:
```
0 9 * * * ~/betting_bot_prod/send_predictions.sh
```

### 4. Test manually
```bash
cd ~/betting_bot_prod
docker exec bet-bot-web python manage.py send_daily_predictions
```

## Admin Workflow

### 1. Create Predictions in Admin

Go to: `https://bet.h2wrestuarantcafe.xyz/admin/predictions/prediction/add/`

Fill in:
- **Fixture**: Select match (e.g., Man City vs Arsenal)
- **Market**: Select market type (e.g., Match Winner, Over/Under)
- **Selection**: Your prediction (e.g., "Man City", "Over 2.5")
- **Odds Value**: Current odds (e.g., 1.85)
- **Package**: Which package gets this prediction (Ordinary, Premium, VIP)
- **Publish At**: Date and time to send (e.g., 2026-03-12 08:00:00)
- **Is Active**: ✓ (checked)

### 2. Schedule Multiple Predictions

Create 5-10 predictions for tomorrow with same `publish_at` date.

Example for March 12, 2026:
```
1. Chelsea vs Liverpool | Match Winner | Chelsea @ 2.10 | Premium | 2026-03-12 08:00
2. Barcelona vs Real Madrid | Over/Under | Over 2.5 @ 1.75 | VIP | 2026-03-12 08:00
3. Man United vs Arsenal | Both Teams Score | Yes @ 1.65 | Ordinary | 2026-03-12 08:00
```

### 3. Automatic Sending

At 8:00 AM on March 12:
- Cron job runs automatically
- System finds all predictions with `publish_at` = today
- Groups predictions by package
- Sends to subscribers based on their package
- Logs results

## Manual Testing

Send predictions for today:
```bash
docker exec bet-bot-web python manage.py send_daily_predictions
```

Send predictions for specific date:
```bash
docker exec bet-bot-web python manage.py send_daily_predictions --date 2026-03-15
```

## Check Logs

```bash
tail -f ~/predictions_broadcast.log
```

## Cron Schedule Examples

```
# Every day at 8:00 AM
0 8 * * * ~/betting_bot_prod/send_predictions.sh

# Every day at 9:30 AM
30 9 * * * ~/betting_bot_prod/send_predictions.sh

# Twice daily: 8 AM and 6 PM
0 8,18 * * * ~/betting_bot_prod/send_predictions.sh

# Only on weekdays at 8 AM
0 8 * * 1-5 ~/betting_bot_prod/send_predictions.sh
```

## What Users Receive

Users with active subscriptions will receive:

```
🔥 DAILY PREDICTIONS 🔥
📅 Tuesday, March 12, 2026
📦 Package: Premium

*1. Chelsea vs Liverpool*
⏰ 20:00
🎯 Prediction: *Chelsea*
💰 Odds: *2.10*
📊 Market: Match Winner

*2. Barcelona vs Real Madrid*
⏰ 21:45
🎯 Prediction: *Over 2.5*
💰 Odds: *1.75*
📊 Market: Over/Under Goals

━━━━━━━━━━━━━━━━━
💡 Bet Responsibly
Good luck! 🍀
```

## Troubleshooting

**No predictions sent:**
- Check if predictions exist for today with `is_active=True`
- Check if users have active subscriptions
- Check logs: `tail -f ~/predictions_broadcast.log`

**Cron not running:**
- Check cron is running: `sudo systemctl status cron`
- Check crontab: `crontab -l`
- Check script permissions: `ls -l send_predictions.sh`

**Users not receiving:**
- Check Telegram bot is running: `docker ps | grep telegram`
- Check user has TelegramProfile
- Check subscription is active and not expired
