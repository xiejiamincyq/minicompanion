# HW-PWR-005-USB-LOGIC — BQ24072T USB source-authorisation review

2026-09-22 Astra follow-up: see [usb-resolution.md](usb-resolution.md). The Type-C high-current suspend question is resolved by USB-IF TD4.10.3. TUSB320LAI VDD must not be connected directly to an unregulated nominal-5V VBUS. The equations below remain a historical Boolean review, not the final wiring instruction; charger input limits must leave headroom for other VBUS loads.

**Status: rejected as a release / fabrication input.**  This is a read-only review of the proposed logic around the existing BQ24072T charge core.  It does not change the charger choice, draw a KiCad circuit, or establish that a USB host is permitted to supply a particular current.

## Proposed Boolean equations, evaluated

Definitions supplied for review:

* `A`: a hardware indication that the source has been identified as permitting at least 500 mA.
* `P`: `MCU_USB_ACTIVE` — enumerating or configured and not suspended; reset/default low.
* `C`: `MCU_USB500` — configured for 500 mA; reset/default low.
* `E1 = A OR NOT P OR C`; `E2 = NOT A AND NOT P`.

The BQ24072T uses `EN2 EN1 = 00` for USB 100 mA, `01` for USB 500 mA, `10` for the resistor-set ILIM range, and `11` for USB suspend/standby.  The proposal must therefore connect `E2 -> EN2` and `E1 -> EN1` to obtain its stated modes.  The following is a Python enumeration of all eight input states, not a hand-derived table:

| A | P | C | E2 E1 | Result |
|---:|---:|---:|:---:|---|
| 0 | 0 | 0 | 11 | USB suspend |
| 0 | 0 | 1 | 11 | USB suspend |
| 0 | 1 | 0 | 00 | USB 100 mA |
| 0 | 1 | 1 | 01 | USB 500 mA |
| 1 | 0 | 0 | 01 | USB 500 mA |
| 1 | 0 | 1 | 01 | USB 500 mA |
| 1 | 1 | 0 | 01 | USB 500 mA |
| 1 | 1 | 1 | 01 | USB 500 mA |

The prior version of this review incorrectly transposed the `EN2 EN1` bit order and reported `A=1, P=0` as ILIM.  The enumeration above corrects that error: it is `01`, USB 500 mA.  Consequently, the stated off behaviour (`A=1`, lost/released `P`) does select USB 500 mA as intended.

However, any `A=1` source remains at USB 500 mA during an MCU suspend/reset interval; the equations do not create `11` for that case.  Whether Type-C CC current advertisement together with USB suspend permits this product-level result needs an applicable USB Type-C / USB data specification citation.  This review has not established it and does **not** use it as a hard rejection basis.  For an ordinary SDP classified with `A=0`, `P=0` selects suspend, consistent with the proposed restriction that an empty/off product must use an identified charging source.

## TUSB320LAI: what it can and cannot supply

The TUSB320LAI can be a UFP CC controller in GPIO mode: `PORT=GND` selects UFP, `ADDR=NC` selects GPIO mode, CC1/CC2 attach to the receptacle, and its `VBUS_DET` requires the specified 900-kOhm link to system VBUS.  In that mode OUT1/OUT2 are open-drain outputs encoding the attached source's Type-C Default / 1.5-A / 3-A CC advertisement.  It has an internal dead-battery `Rd` of 5.1 kOhm ±20% when VDD is absent.  Therefore external 5.1-kOhm CC pull-downs must **not** be paralleled with it.

This only reports CC advertisement.  The TI table explicitly describes Default current as USB 2.0 maximum 500 mA (or USB 3.1 maximum 900 mA).  It does not identify a PC versus a dedicated charger.  A hardware decoder could create `A_CC = medium OR high`, but whether that signal alone may implement the product's off-state USB 500-mA permission remains to be checked against the applicable USB specifications; this document makes no compliance conclusion.

There is also no `A` output while the TUSB320 has no VDD: dead-battery mode provides Rd only.  OUT1/OUT2, `PORT`, `ADDR`, `VBUS_DET`, and OUT pins are non-failsafe when VDD is off; TI warns that they can back-power the part.  Thus the off-charge claim requires an explicitly reviewed always-available supply and reset/pull-up topology for this IC.  It is not established by the candidate.

## BQ24392: useful function and limits

BQ24392 is VBUS-powered and places its DP_CON/DM_CON pins at the connector side and DP_HOST/DM_HOST at the ESP32-S3 side.  It performs DCD plus BC1.2 detection before closing its USB 2.0 switches for SDP/CDP when `GOOD_BAT` is high.  This can keep the MCU from simultaneously driving D+/D− during detection.  The data sheet calls it an IC for micro/mini-USB ports; it does not establish the complete USB-C receptacle / CC interaction as this product's approved Type-C implementation.

It does expose status, so the proposed `A` is not simply unavailable: `CHG_DET` is push-pull and high for a detected DCP/CDP/high-current proprietary charger; `CHG_AL_N` is open drain and low when charging is allowed.  But it is not a universal ≥500-mA authorization bit:

* SDP gives `CHG_DET=LOW` and 100 mA until enumeration changes the permitted current.
* CDP has `CHG_DET=HIGH`, but the result depends on `GOOD_BAT`; data is switched through only when `GOOD_BAT=HIGH`.
* DCP has `CHG_DET=HIGH` but leaves data disconnected.
* If `GOOD_BAT` remains low after a detection, its dead-battery provision timer disables charging after 32 to 45 minutes.  That conflicts with an unattended off-charge requirement unless an independent, reviewed `GOOD_BAT` policy is defined.

The named detector pair therefore has distinct, potentially useful roles (TUSB320LAI for CC and BQ24392 for legacy D+/D− detection/isolation).  BQ24392's `CHG_DET` can be a candidate input to a future reviewed state machine; it cannot be substituted silently for `A` across C-to-C and A-to-C cases.  The unresolved items in this review are its `GOOD_BAT`/DBP behaviour, dead-battery/output availability, data isolation sequence, and unproven Type-C/BC1.2 interoperability—not the corrected Boolean arithmetic.

## Logic-level and default-state review

At 5 V, an SN74AHCT logic gate has TTL-compatible inputs with guaranteed `VIH=2.0 V` and `VIL=0.8 V`; an ESP32-S3 3.18-V high therefore meets the input-high requirement.  This is the suitable 5-V gate family direction for BQ24072T's EN inputs, not an arbitrary 5-V LVC gate whose CMOS threshold must be checked independently.

This observation does **not** make the candidate drawable yet:

* TUSB320 OUT1/OUT2 are open drain.  Their pull-ups must obey the TUSB320 VDD/off-state restrictions.  Pulling a 3.3-V-powered TUSB320 output directly to 5 V is not evidenced here; powering it at 5 V changes all interacting input/pull-up and off-state analysis.
* BQ24392 `CHG_DET` is VBUS-referenced push-pull (specified `VOH >= 3.5 V` at VBUS 4.5–5.5 V).  Its two open-drain status pins need their specified external pull-ups.  Every unpowered-gate and unpowered-detector path needs an Ioff/back-power review before attachment to an always-on BQ24072T EN pin.
* BQ24072T EN inputs must receive a deliberate value through MCU reset, detector start-up (BQ24392 detection is 130–600 ms), cable removal, and MCU suspend.  The stated equations only describe steady Boolean values; they do not give a safe default for all of those intervals.

## Review outcome and required next evidence

Do not integrate this logic into the main schematic or release it for manufacturing.  Before a later independent review sketch can be considered, the owner must provide a complete timing/default-state table, a chosen VDD/pull-up arrangement proving no back-power, a `GOOD_BAT`/DBP policy, and a USB-C/BC1.2 interoperability rationale for the BQ24392 placement.  The specific Type-C/USB-suspend authorization question remains pending an applicable normative source.  This review deliberately does not propose another charger or add circuitry.

## Official sources consulted

* [TI, TUSB320LAI/HAI datasheet, Rev. D](https://www.ti.com/lit/ds/symlink/tusb320lai.pdf): GPIO mode, open-drain OUT1/OUT2, UFP CC current reporting, 900-kOhm VBUS_DET requirement, dead-battery Rd and non-failsafe pin caution.
* [TI, BQ24392 datasheet, Rev. G](https://www.ti.com/lit/ds/symlink/bq24392.pdf): pin functions, BC1.2 flow, output table, GOOD_BAT and DBP timer.
* [TI, SN74AHCT32 datasheet, Rev. O](https://www.ti.com/lit/ds/symlink/sn74ahct32.pdf): 4.5–5.5-V supply and TTL input thresholds.
