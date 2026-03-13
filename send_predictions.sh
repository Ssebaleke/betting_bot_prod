#!/bin/bash
# Daily predictions broadcast script
# Add to crontab: 0 8 * * * /path/to/send_predictions.sh

cd /home/vico/betting_bot_prod
docker exec bet-bot-web python manage.py send_daily_predictions >> /var/log/predictions_broadcast.log 2>&1
