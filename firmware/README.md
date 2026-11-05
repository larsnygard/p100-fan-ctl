# Firmware (ESP32-C3)

The sketch currently runs on the P100 box's flashing machine and is not
yet checked in here.

Required behaviour (the host tools depend on it):

- Serial 115200 8N1 over USB CDC.
- `PWM<n>` (n 0–255): set fan PWM duty.
- `RPM` (query): reply one line `RPM: <value>` from the fan tachometer.
