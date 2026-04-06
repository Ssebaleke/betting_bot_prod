"""
Simple Python scheduler — runs send_daily_predictions every 5 minutes
and check_subscriptions every hour. No cron needed.
"""
import time
import logging
import subprocess
import sys
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SCHEDULER] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

MANAGE = [sys.executable, "manage.py"]
PREDICTIONS_INTERVAL = 5 * 60      # every 5 minutes
SUBSCRIPTIONS_INTERVAL = 60 * 60   # every hour

last_subscriptions_run = 0


def run(command):
    logger.info("Running: %s", " ".join(command))
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            cwd="/app/betting_bot",
        )
        if result.stdout:
            logger.info(result.stdout.strip())
        if result.stderr:
            logger.warning(result.stderr.strip())
    except Exception as e:
        logger.error("Command failed: %s", e)


if __name__ == "__main__":
    logger.info("Scheduler started. Predictions every 5min, subscriptions every 1hr.")
    while True:
        run(MANAGE + ["send_daily_predictions"])

        now = time.time()
        if now - last_subscriptions_run >= SUBSCRIPTIONS_INTERVAL:
            run(MANAGE + ["check_subscriptions"])
            last_subscriptions_run = now

        time.sleep(PREDICTIONS_INTERVAL)
