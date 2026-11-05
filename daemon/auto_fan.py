#!/usr/bin/env python3
import subprocess
import time
import serial

PORT = "/dev/ttyACM0"
BAUD = 115200

MIN_PWM = 150
MAX_PWM = 0
TEMP_LOW = 35
TEMP_HIGH = 50

def get_temp():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "-i", "0", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
            encoding="ascii"
        ).strip()
        return int(out)
    except Exception as e:
        print(f"[WARN] nvidia-smi failed: {e}")
        return None

def calc_pwm(temp):
    if temp is None:
        return 180

    if temp <= TEMP_LOW:
        return MIN_PWM
    if temp >= TEMP_HIGH:
        return MAX_PWM

    ratio = (temp - TEMP_LOW) / (TEMP_HIGH - TEMP_LOW)
    return int(MIN_PWM + (MAX_PWM - MIN_PWM) * ratio)

def open_serial():
    while True:
        try:
            print("[INFO] Connecting to ESP32...")
            ser = serial.Serial(PORT, BAUD, timeout=0.2)
            print("[INFO] Connected.")
            return ser
        except Exception as e:
            print(f"[WARN] Serial connect failed: {e}")
            time.sleep(2)

def send_cmd(ser, cmd):
    try:
        ser.write((cmd + "\n").encode("ascii"))
        ser.flush()
    except Exception as e:
        print(f"[WARN] Serial write failed: {e}")
        raise

def read_rpm(ser):
    try:
        send_cmd(ser, "RPM")
        line = ser.readline().decode("ascii", errors="ignore").strip()
        if line.startswith("RPM:"):
            return line.split("RPM:")[1].strip()
    except Exception as e:
        print(f"[WARN] Serial read failed: {e}")
        raise
    return "?"

def main():
    ser = open_serial()

    while True:
        try:
            temp = get_temp()
            pwm = calc_pwm(temp)

            send_cmd(ser, f"PWM{pwm}")
            rpm = read_rpm(ser)

            print(f"P100 Temp={temp}C PWM={pwm} RPM={rpm}")

        except Exception:
            print("[ERROR] Serial failure, reconnecting...")
            ser.close()
            ser = open_serial()

        time.sleep(1)

if __name__ == "__main__":
    main()

