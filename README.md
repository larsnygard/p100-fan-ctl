# P100 Fan Controller

GPU-cooled PWM fan control for the P100 box: an ESP32-C3 drives the fan,
and a small daemon on the host maps GPU temperature to fan speed.

## Architecture

```
nvidia-smi (GPU temp)                serial (/dev/ttyACM0)
        │                                    │
        ▼                                    ▼
p100-fan.sh ──► owm set fan <pct> ──► ESP32-C3 firmware ──► fan (PWM)
   (host, 3 s poll, hysteresis)         (PWM<n>, RPM report)
```

- **`daemon/p100-fan.sh`** — the fan curve. Polls `nvidia-smi` every 3 s,
  maps temperature to a fan percentage, and applies it with `owm set fan <pct>`.
  A ±5 % hysteresis keeps the fan from oscillating between steps.
- **`daemon/p100-fan.service`** — systemd unit; runs the daemon
  `Restart=always`, `multi-user.target`.
- **`widget/p100-widget.sh`** — one-line status for the desktop bar:
  `P100: 43°C  |  Fan: 30%` (temp from nvidia-smi, fan % via `owm get fan`).
- **`tools/fanctl.py`** — manual tuning TUI over the raw serial link
  (curses; ↑/↓ adjust PWM, live RPM readout). Requires `pyserial`.
- **`firmware/`** — the ESP32-C3 sketch (see below).

## Fan curve

| GPU temp | Fan % |
|---------:|------:|
| < 35 °C  | 20 |
| < 45 °C  | 30 |
| < 55 °C  | 40 |
| < 65 °C  | 55 |
| < 75 °C  | 70 |
| ≥ 75 °C  | 85 |

Step changes are only sent when the new target differs from the last
applied speed by at least 5 %.

## Serial protocol (host ↔ ESP32-C3)

Plain ASCII lines on `/dev/ttyACM0` at 115200 baud:

| Command | Effect |
|---------|--------|
| `PWM<n>` | set fan PWM, `n` = 0–255 |
| `RPM`    | firmware replies `RPM: <value>` |

`owm` (on the P100 host) is the bridge that maps `owm set fan <0-100>`
onto this protocol; `fanctl.py` speaks it directly for manual work.

## Install

```bash
sudo cp daemon/p100-fan.sh /usr/local/bin/
sudo cp widget/p100-widget.sh /usr/local/bin/
sudo cp daemon/p100-fan.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now p100-fan
```

Manual tuning:

```bash
pip install pyserial
python3 tools/fanctl.py          # ↑/↓ = PWM ±10, q = quit
```

## Firmware

The ESP32-C3 sketch is not in this repo yet (it lives on the flashing
machine). Drop it into `firmware/` when located. Known contract it must
satisfy: accept `PWM<n>` (0–255) and reply to `RPM` with `RPM: <value>`.
