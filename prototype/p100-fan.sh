#!/bin/bash

# Avoid fan oscillation
LAST_SPEED=0

while true; do
    TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)

    if   [ "$TEMP" -lt 35 ]; then SPEED=20
    elif [ "$TEMP" -lt 45 ]; then SPEED=30
    elif [ "$TEMP" -lt 55 ]; then SPEED=40
    elif [ "$TEMP" -lt 65 ]; then SPEED=55
    elif [ "$TEMP" -lt 75 ]; then SPEED=70
    else SPEED=85
    fi

    # Hysterese: unngå at vifta hopper opp/ned
    if [ $((SPEED - LAST_SPEED)) -ge 5 ] || [ $((LAST_SPEED - SPEED)) -ge 5 ]; then
        owm set fan $SPEED
        LAST_SPEED=$SPEED
    fi

    sleep 3
done

