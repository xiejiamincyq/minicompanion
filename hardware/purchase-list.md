# Purchase List

Complete parts list for the Devotchi portable device. Parts are split into two categories: PCB-assembled (ordered through JLCPCB) and separately-sourced (ordered directly).

## PCB-Assembled Parts (JLCPCB BOM)

These parts are placed on the PCB by JLCPCB during assembly. The LCSC part numbers are used for ordering.

### ICs & Modules

| Ref | Description | Value | LCSC | Library | Price (1+) |
|---|---|---|---|---|---|
| U101 | MCU | ESP32-S3-MINI-1-N4R2 | C3013941 | Extended | $5.01 |
| U202 | LiPo charger | TP4056-42-ESOP8 | C725790 | Extended | $0.06 |
| U201 | Battery protection IC | DW01A | C351410 | Extended | $0.04 |
| U203 | 3.3V LDO regulator | ME6211C33M5G-N | C82942 | Extended | $0.05 |

### Transistors & Diodes

| Ref | Description | Value | LCSC | Library | Price (1+) |
|---|---|---|---|---|---|
| Q201 | Battery protection MOSFET | FS8205A | C2830320 | Extended | $0.05 |
| Q301, Q401 | Backlight / motor driver | AO3400A (x2) | C20917 | Basic | $0.08 |
| D401 | Motor flyback diode | 1N5819W | C42441798 | Extended | $0.007 |
| D402 | Debug status LED (green) | FC-1608G1-520 | C19189745 | Extended | $0.006 |

### Connectors

| Ref | Description | Value | LCSC | Library | Price (1+) |
|---|---|---|---|---|---|
| J201 | USB-C connector | HRO TYPE-C-31-M-12 | C165948 | Extended | $0.18 |
| J202 | Battery connector (SMD) | PH 2.0mm 2-pin SMD right-angle | C7433648 | Extended | $0.02 |
| FPC301 | Display FPC connector | JUSHUO AFC01-S12FCA-00 | C262661 | Extended | $0.09 |

### Capacitors (all MLCC ceramic)

| Ref | Value | Package | LCSC | Library | Price (1+) |
|---|---|---|---|---|---|
| C101 | 22µF | 0805 | C45783 | Basic | $0.03 |
| C201, C202 | 10µF (x2) | 0805 | C15850 | Basic | $0.02 |
| C103, C204, C205, C301, C302 | 1µF (x5) | 0603 | C15849 | Basic | $0.007 |
| C102, C203, C501, C502, C504 | 100nF (x5) | 0603 | C14663 | Basic | $0.003 |

### Resistors (all 0603, ±1%)

| Ref | Value | LCSC | Library | Price (1+) |
|---|---|---|---|---|
| R101, R206, R501, R502, R504 | 10kΩ (x5) | C25804 | Basic | $0.001 |
| R207, R208 | 100kΩ (x2) | C25803 | Basic | $0.001 |
| R203, R204 | 5.1kΩ (x2) | C23186 | Basic | $0.001 |
| R205 | 3kΩ | C4211 | Basic | $0.001 |
| R201, R202, R302, R402 | 1kΩ (x4) | C21190 | Basic | $0.001 |
| R401 | 150Ω | C22808 | Basic | $0.001 |
| R301 | 22Ω | C23345 | Basic | $0.001 |

### Switches

| Ref | Description | Value | LCSC | Library | Price (1+) |
|---|---|---|---|---|---|
| SW101 | MCU reset button | TS-1187A-B-A-B | C318884 | Basic | $0.02 |
| SW501-SW504 | User buttons (x4) | TS-1187A-B-A-B | C318884 | Basic | $0.02 |

### Other

| Ref | Description | LCSC | Notes |
|---|---|---|---|
| J401 | Motor solder pads (Conn_01x02) | — | Not assembled, solder motor wires manually |
| TP101-TP504 | Test points (x30) | — | Bare pads, no part needed |

---

## Separately-Sourced Parts

These parts are not assembled on the PCB. Order them separately and connect during final assembly.

### Display

| Part | Description | Source | Price | Notes |
|---|---|---|---|---|
| HS20HS072RX | 2.0" IPS TFT LCD, 320x240, ST7789 | [LCSC C5329582](https://www.lcsc.com/product-detail/lcd-screen_hs-hs20hs072rx_C5329582.html) | $3.70 (1+), $2.49 (100+) | Connects via FPC cable to FPC301 |

### Vibration Motor

| Part | Description | Source | Price | Notes |
|---|---|---|---|---|
| LCM0720A3134F | 6mm coin vibration motor, 3V, 85mA | [LCSC C2895081](https://www.lcsc.com/product-detail/C2895081.html) | $0.64 | Solder lead wires to J401 pads |

### Battery

| Part | Description | Source | Price | Notes |
|---|---|---|---|---|
| LiPo battery | 3.7V, 300-500mAh, JST PH 2-pin connector | AliExpress / Amazon | ~$3-5 | Must have JST PH connector to match J202 |

### FPC Cable (if not included with display)

| Part | Description | Source | Price | Notes |
|---|---|---|---|---|
| FPC cable | 12-pin, 0.5mm pitch, same-side contacts | AliExpress | ~$0.50 | Verify contact side matches FPC301 (bottom contact) |

### Enclosure

| Part | Description | Source | Price | Notes |
|---|---|---|---|---|
| 3D printed case | PLA/PETG/ABS, custom design | Self-printed or JLCPCB 3D printing | ~$2-5 | Design after PCB layout is finalized |

---

## Cost Estimate (per unit, at 50 units)

| Category | Estimated Cost |
|---|---|
| PCB fabrication (JLCPCB) | ~$2-3 |
| PCB assembly (components + placement) | ~$8-10 |
| Display | ~$3 |
| Motor | ~$0.50 |
| Battery | ~$3-5 |
| Case | ~$2-5 |
| **Total per unit** | **~$19-28** |
