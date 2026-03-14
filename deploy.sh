#!/bin/bash
# deploy.sh - Pull latest code and rebuild containers

set -e

cd ~/betting_bot_prod

echo "=== Pulling latest code ==="
git pull

echo "=== Rebuilding containers ==="
docker-compose down
docker-compose build --no-cache web
docker-compose up -d

echo "=== Waiting for containers to start ==="
sleep 20

echo "=== Running migrations ==="
docker exec bet-bot-web python manage.py migrate

echo "=== Testing notification ==="
docker exec bet-bot-web python manage.py shell -c "
from bots.notifications import send_telegram_message
result = send_telegram_message(1944965209, '✅ Bot redeployed successfully!')
print('Notification test:', result)
"

echo "=== Deployment complete ==="
docker-compose ps
