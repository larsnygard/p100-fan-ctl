# P100 Fan Controller

GPU-cooled PWM fan control for the P100 box: an ESP32-C3 drives the fan,
and a daemon on the host maps GPU temperature directly to fan PWM over
serial. Live and running on the box.

## Architecture

```
nvidia-smi -i 0 (GPU temp)      serial /dev/ttyACM0, 115200
        │                                │
        ▼                                ▼
auto_fan.py ──── PWM<n> ────► ESP32-C3 firmware ────► fan
  (1 s loop,                  (USB CDC; replies
   auto-reconnect)             RPM: <value>)
```

- **`daemon/auto_fan.py`** — the live controller (systemd `auto-fan.service`,
  running since Oct 24). Reads GPU 0 temp every second, computes PWM,
  sends it, then queries RPM for the log line
  `P100 Temp=36C PWM=140 RPM=2310`. Reconnects the serial port on any
  failure.
- **`daemon/auto-fan.service`** — systemd unit, `Restart=always`, runs as root.
- **`widget/p100-widget.sh`** — desktop status line:
  `P100: 43°C  |  Fan: 30%` (via `owm get fan` on the P100 host).
- **`tools/fanctl.py`** — manual tuning TUI over the raw serial link
  (curses; ↑/↓ adjust PWM 0–255 by ±10, live RPM readout). Requires `pyserial`.
- **`prototype/`** — an earlier bash version that stepped fan % via an
  `owm set fan` bridge with 5 % hysteresis, superseded by the direct
  Python controller.
- **`firmware/`** — the ESP32-C3 sketch (see below).

## Fan curve

Linear interpolation between two temperature breakpoints
(as implemented in `calc_pwm`):

| GPU temp | PWM sent | Fan |
|---------:|---------:|-----|
| ≤ 35 °C  | 150 (`MIN_PWM`) | minimum |
| ≥ 50 °C  | 0 (`MAX_PWM`)   | full |
| between  | 150 → 0 linearly | ramps up |

Note the inverted scale: **lower PWM value = faster fan**. Mid-temps
match the live log, e.g. 36 °C → PWM 140, ~2310 RPM. If the GPU read
fails, it falls back to PWM 180.

## Serial protocol (host ↔ ESP32-C3)

Plain ASCII lines, 115200 8N1 over USB CDC:

| Command | Effect |
|---------|--------|
| `PWM<n>` | set fan PWM (n 0–255) |
| `RPM`    | firmware replies `RPM: <value>` |

## Install

```bash
sudo cp daemon/auto_fan.py /usr/local/bin/
sudo cp daemon/auto-fan.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now auto-fan
```

Requires `python3` + `pyserial` and `nvidia-smi` on the host.

Manual tuning:

```bash
pip install pyserial
python3 tools/fanctl.py          # ↑/↓ = PWM ±10, q = quit
```

## Firmware

The ESP32-C3 sketch is not in this repo yet (it lives on the flashing
machine). Drop it into `firmware/` when located. Known contract it must
satisfy: accept `PWM<n>` (0–255) and reply to `RPM` with `RPM: <value>`.
