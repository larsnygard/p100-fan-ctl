#!/usr/bin/env python3
import sys
import time
import serial
import curses

PORT = "/dev/ttyACM0"
BAUD = 115200

START_PWM = 180      # lav hastighet ved oppstart
STEP = 10            # endring per tastetrykk
MIN_PWM = 0
MAX_PWM = 255

def send_cmd(ser, cmd):
    ser.write((cmd + "\n").encode("ascii"))
    ser.flush()

def read_lines(ser):
    lines = []
    ser.timeout = 0.05
    try:
        while True:
            line = ser.readline()
            if not line:
                break
            lines.append(line.decode("ascii", errors="ignore").strip())
    except Exception:
        pass
    return lines

def main(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
    except Exception as e:
        stdscr.addstr(0, 0, f"Kunne ikke åpne {PORT}: {e}")
        stdscr.refresh()
        time.sleep(3)
        return

    pwm = START_PWM
    send_cmd(ser, f"PWM{pwm}")
    time.sleep(0.2)

    while True:
        stdscr.erase()
        stdscr.addstr(0, 0, "ESP32-C3 Fan Controller (↑/↓ = PWM, q = quit)")
        stdscr.addstr(2, 0, f"Port: {PORT}")
        stdscr.addstr(3, 0, f"PWM:  {pwm}")

        # be om RPM
        send_cmd(ser, "RPM")
        time.sleep(0.05)
        lines = read_lines(ser)

        rpm_value = "?"
        for line in lines:
            if line.startswith("RPM:"):
                rpm_value = line.split("RPM:")[-1].strip()
        stdscr.addstr(4, 0, f"RPM:  {rpm_value}")

        # vis rå linjer under
        row = 6
        for line in lines:
            stdscr.addstr(row, 0, line[:80])
            row += 1

        stdscr.refresh()

        ch = stdscr.getch()
        if ch == ord('q'):
            break
        elif ch == curses.KEY_UP:
            pwm = min(MAX_PWM, pwm + STEP)
            send_cmd(ser, f"PWM{pwm}")
        elif ch == curses.KEY_DOWN:
            pwm = max(MIN_PWM, pwm - STEP)
            send_cmd(ser, f"PWM{pwm}")

        time.sleep(0.1)

    ser.close()

if __name__ == "__main__":
    curses.wrapper(main)

