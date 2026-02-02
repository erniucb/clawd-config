#!/bin/bash
# Twitter监控脚本

cd /root/clawd

while true; do
  echo "=== $(date) - 扫描Twitter ===" >> /tmp/twitter-monitor.log
  DISPLAY=:1 timeout 60 node /root/clawd/scripts/twitter-scrape-once.js >> /tmp/twitter-monitor.log 2>&1
  sleep 60
done
