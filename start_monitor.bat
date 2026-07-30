@echo off
title Apple Store Pickup Monitor 24/7
cd /d "%~dp0"
set TELEGRAM_TOKEN=5954357064:AAEHIBucPDlgMthnDi7COBFDA0R_7aTsCzs
set TELEGRAM_CHAT_ID=1008857254,-1002458379798,601135012
set PICKUP_INTERVAL=120
echo Starting Apple Store Pickup Monitor (checking every 2 minutes)...
python monitor_daemon.py
pause
