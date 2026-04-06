#!/bin/bash
set -e

printenv | grep -v "^_" > /etc/environment

cat > /etc/cron.d/predictions << 'EOF'
*/5 * * * * root . /etc/environment && cd /app/betting_bot && python manage.py send_daily_predictions >> /var/log/predictions.log 2>&1
0 * * * * root . /etc/environment && cd /app/betting_bot && python manage.py check_subscriptions >> /var/log/subscriptions.log 2>&1
EOF

chmod 0644 /etc/cron.d/predictions
touch /var/log/predictions.log /var/log/subscriptions.log

echo "Scheduler starting cron..."
cat /etc/cron.d/predictions

cron && tail -f /var/log/predictions.log
