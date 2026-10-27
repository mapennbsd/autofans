# dawg hardware: wiring, power, and the three-fan plan

Written 2026-10-27. The current wiring works, but it is a known
compromise. The plan below is to be built when a third fan is added.

## Current wiring

- dawg: Raspberry Pi 3 Model B Rev 1.2, on an Argon 5.25V 3A micro-USB
  supply.
- Adafruit EMC2101 (STEMMA QT) at 0x4c and MCP9808 at 0x18, on I2C bus 1.
  The board's power and ground come from the Pi over STEMMA QT.
- Two Noctua NF-A14 5V PWM fans on a USB power cable plugged into one of
  dawg's USB ports, split to both fans. The cable's 5V and ground go
  straight to the fans and never touch the EMC2101. The EMC2101's FAN pin
  drives the cable's PWM wire, and its TACH pin reads the cable's tach
  wire.
- The PWM and tach signals share a ground only because the fans' ground
  *is* the Pi's ground, through the USB port.
- The RPM is one tach signal. It does not confirm that both fans are
  running (see DEPLOYMENT.md).

## Known issue: undervoltage

On 2026-10-27 dawg logged 86 `Undervoltage detected` events in 15 hours,
each lasting 4–6 s. Almost all came right after underdog's 5-minute
`check-run` (or `gather-run`). How often they happen follows the fan PWM:
about 1 an hour at 60%, 2 at 70%, and 6–11 at 80–100%. A 60 s CPU load on
all four cores at 60% PWM did not trigger one.

The supply's current rating is not the problem. The fan current flows in
through the Pi's micro-USB jack, input fuse and USB rail, and back out a
USB port. At about 1–1.3A, the voltage drop on that path uses up the
roughly 0.6V margin between 5.25V and the Pi's ~4.63V undervoltage
threshold. The cure is to take the fans off the Pi's power, which is part
of the plan below. Until then the events are tolerated: they are short,
and they throttle the CPU only while they last.

## Plan for three fans

| What | Design |
| --- | --- |
| PWM | One EMC2101 FAN output to all three fans' PWM wires. PWM inputs draw no real current, so one output can drive several fans. |
| Power | A dedicated 5V USB charger (2A or more) for all three fans, on the same UPS as dawg. Nothing on dawg's USB ports. |
| Ground | One thin wire (22–26 AWG) from the EMC2101's GND pin to the fans' ground. It carries only signal current. Without it, a charger's isolated output floats, and PWM and tach have no reference. |
| Tach | Each fan's tach wire goes to its own Pi GPIO with the internal pull-up to 3.3V, for example GPIO 17, 27 and 22 (pins 11, 13 and 15). The tach outputs only pull to ground, so no 5V reaches a GPIO. At most 1500 RPM with 2 pulses per revolution, that is about 50 Hz. |
| 5V | The charger's 5V never connects to the Pi's 5V. |

Not one EMC2101 per fan: its address is fixed at 0x4c, so more than one
needs an I2C multiplexer or extra buses, and only to get extra tach inputs.

Software changes, made at the same time as the wiring:

- autofans counts tach pulses on the three GPIOs (lgpio edge callbacks).
- The state file reports one RPM per fan.
- underdog's `fans` check alerts when any single fan stops or slows.

After the change, `vcgencmd get_throttled` should stay `0x0`, and
`journalctl -k -b | grep -c "Undervoltage detected"` should stay 0.
