#!/usr/bin/env bash

echo "data now : $(date +%Y-%m-%d)"
echo "data now : $(date +%H:%M)"

at -f recording.sh 11:30 "$(date +%Y-%m-%d)"
at -f recording.sh 12:00 "$(date +%Y-%m-%d)"
at -f recording.sh 12:30 "$(date +%Y-%m-%d)"
at -f recording.sh 13:00 "$(date +%Y-%m-%d)"
at -f recording.sh 13:30 "$(date +%Y-%m-%d)"
at -f recording.sh 14:00 "$(date +%Y-%m-%d)"
at -f recording.sh 14:30 "$(date +%Y-%m-%d)"
at -f recording.sh 15:00 "$(date +%Y-%m-%d)"
at -f recording.sh 15:30 "$(date +%Y-%m-%d)"
at -f recording.sh 16:00 "$(date +%Y-%m-%d)"
at -f recording.sh 16:30 "$(date +%Y-%m-%d)"
at -f recording.sh 17:00 "$(date +%Y-%m-%d)"
at -f recording.sh 17:30 "$(date +%Y-%m-%d)"
at -f recording.sh 18:00 "$(date +%Y-%m-%d)"

