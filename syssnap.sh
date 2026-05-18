#!/bin/bash
echo "=== LOAD ===" && cat /proc/loadavg
echo "=== MEMORY ===" && free -h
echo "=== CPU TEMP ===" && sensors 2>/dev/null
echo "=== TOP PROCS ===" && ps aux --sort=-%cpu | head -20
echo "=== DISK IO ===" && iostat -x 1 2 2>/dev/null
echo "=== NET ===" && cat /proc/net/dev
