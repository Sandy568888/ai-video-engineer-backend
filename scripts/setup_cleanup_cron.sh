#!/bin/bash
# Setup cron job for Wasabi cleanup

echo "Setting up Wasabi cleanup cron job..."

# Create cron job (runs daily at 2 AM)
CRON_JOB="0 2 * * * cd /app && /usr/bin/python3 scripts/cleanup_wasabi.py >> /var/log/wasabi_cleanup.log 2>&1"

# Add to crontab
(crontab -l 2>/dev/null | grep -v "cleanup_wasabi.py"; echo "$CRON_JOB") | crontab -

echo "✅ Cron job installed: Daily cleanup at 2 AM"
echo "To view cron jobs: crontab -l"
echo "To view logs: tail -f /var/log/wasabi_cleanup.log"
