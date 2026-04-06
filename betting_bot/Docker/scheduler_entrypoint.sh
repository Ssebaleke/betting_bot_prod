#!/bin/bash
set -e

# Export env vars for cron
printenv | grep -v "^_" > /etc/environment

# Write cron jobs
cat > /etc/cron.d/predictions << 'EOF'
*/5 * * * * root . /etc/environment && cd /app/betting_bot && python manage.py send_daily_predictions >> /var/log/predictions.log 2>&1
0 * * * * root . /etc/environment && cd /app/betting_bot && python manage.py check_subscriptions >> /var/log/subscriptions.log 2>&1
EOF

chmod 0644 /etc/cron.d/predictions
touch /var/log/predictions.log /var/log/subscriptions.log

echo "Scheduler starting..."
echo "Cron job:"
cat /etc/cron.d/predictions

# Start cron in foreground
cron && tail -f /var/log/predictions.log
