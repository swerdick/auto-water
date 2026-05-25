# Hardware Inventory

A catalog of the parts on hand for the next iteration of Auto-Water (the
samwise / Raspberry Pi 5 build). Compiled from a photo dig through the
old Raspberry Pi / Arduino parts boxes on **2026-05-23**.

> **Quantities and exact part numbers are best-effort estimates from photos.**
> Items flagged ❓ need a closer look in person — see
> [Needs Confirmation](#needs-confirmation) at the bottom.

Photos are numbered 1–17 in the order they were shared; the **Photo** column
points back to where each item appears so you can cross-check.

---

## Soil moisture sensors (two types — as expected)

| Item | Qty | Interface | Photo | Notes |
|------|-----|-----------|-------|-------|
| **Resistive soil moisture probe** (forked PCB, "moisture detection") | several (5+) | Analog + digital (via comparator board) | 1, 2, 3, 14 | Classic two-prong type. Corrodes over time; legacy from the original Kuman 5-pack (see `COSTS.md`). **The bagged boards in photos 1–2 turned out to be more of these probes** — the plated holes running down each prong read as "segments" in the photo. |
| **LM393 comparator board** (blue, AO/DO/GND/VCC, trimpot) | 1+ | **DO = digital wet/dry** (GPIO), AO = analog | 3 | Pairs with the resistive probe. The DO pin gives a thresholded wet/dry signal readable directly on a Pi GPIO — **no ADC needed**. |
| **Capacitive soil moisture sensor** ("DIY", 5 pcs) | 5 (per label) | **Analog voltage out** | 8 | Corrosion-resistant, the better long-term choice. Outputs an analog level → **needs an ADC** on the Pi 5 (no onboard ADC). |

## Temperature sensors

| Item | Qty | Interface | Photo | Notes |
|------|-----|-----------|-------|-------|
| **DS18B20 waterproof temperature probe** (HiLetgo, 5 pcs) | 5 (per label) | **1-Wire** (digital) | 7 | Stainless probe on a lead — ideal for soil temperature. 1-Wire works great on the Pi 5 (`w1-gpio` overlay). Multiple probes share one GPIO pin. |

## Environmental sensors

| Item | Qty | Interface | Photo | Notes |
|------|-----|-----------|-------|-------|
| **Adafruit HDC3022** Temperature + Humidity (P59989 / adafru.it/5989) | 1 | **I²C** (STEMMA QT) | 4, 5, 6 | Air temp + relative humidity. I²C addr 0x44/0x45. STEMMA QT = plug-and-play Qwiic connector. |
| **GY-302 / BH1750** ambient light (lux) sensor | 1 | **I²C** | 5, 6 | Light level in lux. I²C addr 0x23 (or 0x5C). Useful for correlating watering with light/season. |

> All three environmental/temperature sensors are **digital (I²C / 1-Wire)** —
> they sidestep the Pi-5-has-no-ADC problem entirely. Only the *capacitive soil
> sensors* need an ADC. See [Key constraint](#key-constraint-pi-5-has-no-adc).

## Actuators & water handling

| Item | Qty | Voltage/Drive | Photo | Notes |
|------|-----|---------------|-------|-------|
| **Solenoid valve "FPD180"** (white plastic, push-fit ports) | 1 | **12 V DC**, 0.02–1.0 MPa | 1, 2 | On/off water valve. Switch via a relay (the owned 8-ch relay is currently missing — see below). Needs 12 V supply + a flyback diode. **Confirmed it does *not* mate directly with the pump** — treat valve and pump as two independent watering paths joined by tubing, not one assembly. |
| **Small pump** (black round housing — "aquarium-pump-looking") | 1 | DC motor-driven | 1, 2, 15, 16 | Self-priming-style pump for moving water from a reservoir. Independent of the solenoid valve. Likely pairs with one of the DC motors below. |
| **DC motor** ("T T MOTOR", metal can; barcode 9352165550) | 1–2 | DC (likely 3–12 V) | 1, 18 | Plain brushed can motor. Needs a motor driver / MOSFET (relays aren't ideal for PWM). Photo 18 shows it beside a smaller black motor/pump unit with red/white leads. |
| **DC Motor / Servo Motor kit** (boxed) | 1 box | — | 14 | ❓ Likely a small DC motor + SG90-class servo from an Arduino kit. Confirm contents. |

## Display

| Item | Qty | Interface | Photo | Notes |
|------|-----|-----------|-------|-------|
| **Liquid Crystal Display** — 16×2 (1602) character LCD | 1 | **16-pin parallel HD44780** (no I²C backpack) | 15, 19, 20 | Confirmed: single-row 16-pin header, two COB driver chips on the back, no backpack. Parallel mode needs ~6 GPIO (4-bit) + a contrast pot; a ~$1 PCF8574 I²C backpack would drop it to 2 pins if GPIO gets tight. |

## Tubing & fittings

| Item | Qty | Photo | Notes |
|------|-----|-------|-------|
| **Clear flexible vinyl/silicone tubing** (large coil) | 1 coil (long) | 17 | Main water line. Measure ID/OD so fittings, pump head, and valve ports all match. |
| **Push-fit quick-connect fittings** (white body, blue collets) | several | 1 | John-Guest-style, for ~1/4" RO tubing. Confirm they match the tubing OD. |
| **Barbed connectors** (clear plastic, straight / T / Y) | a handful | 1 | For joining/splitting tube runs. |

## Compute & prototyping

| Item | Qty | Photo | Notes |
|------|-----|-------|-------|
| **Raspberry Pi 2 Model B** v1.1 (2014, clear Vilros case) | 1 | 30, 33–36 | ✅ Found 2026-05-24 with the 8-ch relay + original resistive sensors still wired. ARMv7 **32-bit**, quad-core A7, 1 GB RAM, Edimax USB WiFi, 40-pin header. **Won't join k3s** (32-bit / 1 GB / multi-arch burden) — but a great standalone **actuation bench rig**: classic RPi.GPIO stack, runs the same `auto_water` app via systemd. |
| **Raspberry Pi** (red/white case, photo 13) | 1 | 13 | ❓ A separate older Pi — confirm model. The build target is `samwise` (Pi 5), already a k3s worker. |
| **Arduino starter kit** | 1 | 3, 7, 12 | Source of many of the loose sensors/parts here. Handy as a bench test rig / second brain. |
| **Breadboards** (full-size, half, mini) | 3+ | 13 | Prototyping. |

## Wiring, connectors & passives

| Item | Qty (est.) | Photo | Notes |
|------|-----------|-------|-------|
| **Dupont jumper wires** (M-M, M-F, F-F) + 40-pin ribbon | lots | 9, 10, 12 | More than enough. |
| **Alligator-clip test leads** (insulated, multicolor) | ~8–10 | 4, 10, 16 | Quick bench connections. |
| **Resistors** (assorted, axial, on tape strips) | assorted | 10 | For pull-ups/downs, LED current limiting, the DS18B20 4.7 kΩ 1-Wire pull-up, etc. |
| **TICONN Solder & Seal wire connectors** (100 pcs) | 1 box (100) | 15, 16 | Heat-shrink solder butt splices — **waterproof** joints for anything that gets wet near the plant/reservoir. |
| **Passives grab-bag** (LEDs, transistors, diodes, capacitors, standoffs) | bin | 11 | General electronics stock. Transistors/MOSFETs here may drive the pump motor. |
| **Heat-shrink / misc tubing** (green loop) | some | 11 | Insulation / strain relief. |
| ❓ **Honeywell-labeled black part** | 1 | 7 | Unidentified. Could be a Honeywell pressure/humidity sensor. Confirm. |

## Documented as owned but not clearly pictured

These appear in the original `COSTS.md` / project-hub overview but aren't obvious
in the photos — worth locating before the build:

- **5 V 8-channel relay module** — ✅ **FOUND** (2026-05-24, under the bed, still wired to the original Pi). SONGLE `SRD-05VDC-SL-C`, opto-isolated, with a JD-VCC jumper — exactly the good kind, and the board that worked in v1. No need to rebuy.
- **12 V power supply adapters** (2-pack, with +/- leads for jumper cables) — to power the solenoid/motor.
- Additional Kuman KY70-series moisture sensors (original 5-pack).

---

## Key constraint: Pi 5 has no ADC

The Raspberry Pi 5 has **no analog input**. That sorts the sensors into two groups:

- **Plug-and-play (digital):** DS18B20 (1-Wire), HDC3022 (I²C), BH1750 (I²C), and
  the resistive sensor's **DO** pin (digital wet/dry). These work directly.
- **Needs an ADC:** the **capacitive** soil sensors output an analog voltage. To
  read actual moisture *levels* (not just wet/dry) you'll want an **ADS1115**
  (I²C, 16-bit) or **MCP3008** (SPI, 10-bit). Neither is in this inventory — it's
  the main thing to buy. The ADS1115 is the easier choice (shares the I²C bus
  the HDC3022/BH1750 already use).

## Likely still needed (gaps)

| Need | Why | Specific pick |
|------|-----|---------------|
| **ADC** | Read capacitive soil-moisture *levels* on the Pi 5 (no onboard ADC) | **ADS1115** — 16-bit, 4-ch, I²C (addr 0x48). Rides the existing I²C bus. Buy a 2–3 pack. Power capacitive sensors at 3.3 V so output stays ≤ ADC rail. |
| ~~Relay module~~ | Switch the 12 V solenoid valve on/off | ✅ **No longer needed — the 8-ch SONGLE board turned up.** It's opto-isolated, active-LOW, with a JD-VCC jumper, so 3.3 V GPIO drives it fine (that's why v1 worked — my earlier "bad cheap relay" guess was wrong). |
| **Motor driver** (optional) | PWM speed / on-off for the DC pump motor (relays can't PWM) | Logic-level MOSFET (IRLZ44N — or from the bin) or a DRV8871 board. |
| **STEMMA QT cable** (optional) | Solderless hookup for the HDC3022's JST-SH port | STEMMA QT / Qwiic → male-header jumper cable. |
| **Flyback diode** | Protect the driver when switching the inductive valve/motor coil | 1N4007 across the coil — **you have diodes in the bin** (photo 11). |
| **Water reservoir** | Source for pump/valve | Any food-safe container. |
| **Level sensor** (stretch) | Detect empty reservoir | Float switch. |

---

## Needs confirmation

Quick in-person checks to firm up this inventory:

**Resolved 2026-05-23:** ~~LCD~~ → 16×2 parallel HD44780 (photos 19–20); ~~segmented board~~ → more resistive probes; ~~valve↔pump mating~~ → they don't, independent paths.

Still open:

- **DC Motor / Servo kit** (photo 14) — what's actually in the box?
- **Honeywell part** (photo 7) — what is it?
- **Tubing dimensions** (photo 17) — ID/OD, so pump/valve/fittings all match.
- **Pictured Pi** (photo 13) — which model, and is it spare?
- **8-ch relay** — keep hunting; rebuy if it doesn't surface. **12 V supplies** — locate (listed in `COSTS.md`).
