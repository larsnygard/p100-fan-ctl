#!/bin/bash

TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)
FAN=$(owm get fan | tr -dc '0-9')

echo "P100: ${TEMP}°C  |  Fan: ${FAN}%"

