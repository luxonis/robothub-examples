#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pids=$(ps aux | grep ros | grep -v -e 'grep' -e 'ros_kill.sh' | awk '{print $2}')

for pid in $pids; do
    process_info=$(ps aux | grep " $pid " | grep -v grep)
    echo "Process associated with PID $pid:"
    echo -e "${YELLOW}$process_info${NC}"
    read -p "Do you want to kill this process? (y/n): " choice
    if [ "$choice" == "n" ]; then
        echo -e "${GREEN}Process with PID $pid not killed.${NC}"
    else
        kill -9 "$pid"
        echo -e "${RED}Process with PID $pid killed.${NC}"
    fi
    echo
    echo
done
