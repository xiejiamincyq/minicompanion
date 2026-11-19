# Devotchi Case — Dimensions Reference

All dimensions in mm. Use this as a reference when recreating the design in Onshape/Fusion/etc.

## Case Outer Dimensions

| Dimension | Value | Notes |
|---|---|---|
| Width | 60.0 | Clean number, display (51.8) + walls + clearance (4.8) |
| Height | 60.0 | Display zone (39.2) + button zone (15.8) + USB zone (5.0) |
| Depth | 15.1 | See depth stack below |
| Corner radius | 3.0 | XY plane, all 4 corners |
| Front chamfer | 2.5 | 45-degree slope on front face edges only |
| Back cover chamfer | 1.0 | 45-degree slope on back face edges |
| Wall thickness | 1.5 | All walls |

## Depth Stack (front to back, Z axis)

```
Front wall ──────── 1.5mm   Z = 0 to 1.5
Display ─────────── 2.5mm   Z = 1.5 to 4.0
Gap (ESP32) ─────── 2.5mm   Z = 4.0 to 6.5
PCB ─────────────── 1.6mm   Z = 6.5 to 8.1
Gap ─────────────── 0.5mm   Z = 8.1 to 8.6
Battery ─────────── 5.0mm   Z = 8.6 to 13.6
Back wall ────────── 1.5mm   Z = 13.6 to 15.1
```

## Front View Layout (Y axis, top to bottom)

```
┌──────────────────────────────────────┐ Y = 0
│           CASE TOP WALL (1.5)        │
│  ┌────────────────────────────────┐  │ Y = 1.5
│  │                                │  │
│  │   Display window (40.8 x 30.6)│  │
│  │   Centered in display zone     │  │
│  │                                │  │
│  └────────────────────────────────┘  │
│          Display zone: 39.2mm        │ Y = 39.2
│                                      │
│  <approve> <action>  <reject>        │ Y = 43.9 (btn centers)
│                                      │
│         Button zone: 15.8mm         │
│     (LED)     ═══USB═══             │
│          USB zone: 5.0mm             │ Y = 60.0
└──────────────────────────────────────┘
```

## Display

| Dimension | Value | Notes |
|---|---|---|
| Module size | 51.8 x 36.2 x 2.5 | HS20HS072RX |
| Active area | 40.8 x 30.6 | Window cutout size |
| FPC tail | 6.5 wide, 12.1 long | Exits LEFT edge, centered on display Y |
| Pocket size | 55.2 x 36.2 | Full inner cavity width/height |
| Pocket depth | 3.0 | From Z=1.5 to Z=4.5 |
| Window bezel slope | 1.5mm margin, 0.8mm deep | Sloped surround on front face |

### Display Retention Clips (5 total)

Thin lips (1.5mm overhang, 1.0mm thick) at Z = 3.0 (back of display).

| Clip | Position | Size |
|---|---|---|
| Left top | X = pocket edge, Y = 1mm from top | 1.5 x 5.0 |
| Left bottom | X = pocket edge, Y = 20.3mm from top | 1.5 x 5.0 |
| Right top | X = pocket far edge, Y = 1mm from top | 1.5 x 5.0 |
| Right bottom | X = pocket far edge, Y = 20.3mm from top | 1.5 x 5.0 |
| Top | Centered on top edge | 8.0 x 1.5 |

Left clips split to avoid FPC exit zone.

## PCB

| Dimension | Value | Notes |
|---|---|---|
| Size | 45.0 x 50.0 x 1.6 | Extended height for FPC connector clearance |
| Position X | 7.5 | Centered: (60.0 - 45.0) / 2 |
| Position Y | 8.5 | Bottom-aligned: 60.0 - 1.5 - 50.0 |
| Position Z | 6.5 | Components face front (toward display) |

### FPC Connector (AFC01-S12FCA-00)

| Dimension | Value | Notes |
|---|---|---|
| PCB X | 5.0 | From left edge (origin), no overhang |
| PCB Y | 38.9 | From bottom edge, aligned with display center |
| Rotation | -90° | Latch faces left (cable entry from PCB edge) |
| Body extends | 4.5mm left, 2mm right of origin | After rotation |

### Button Switches (3x TS-1187A, 6x6mm)

| Button | PCB X | PCB Y (from bottom) | Case X | Case Y |
|---|---|---|---|---|
| Approve (SW501) | 8.5 | 14.6 | 16.0 | 43.9 |
| Action (SW502) | 22.5 | 14.6 | 30.0 | 43.9 |
| Reject (SW503) | 36.5 | 14.6 | 44.0 | 43.9 |

14mm center-to-center spacing. Wake function handled by any button press (RTC wake).

### Mounting Holes (3x M2)

| Hole | PCB X | PCB Y | Notes |
|---|---|---|---|
| TR | 42.0 | 47.0 | 3mm inset from edges |
| BL | 3.0 | 3.0 | 3mm inset from edges |
| BR | 42.0 | 3.0 | 3mm inset from edges |

TL hole removed for FPC connector clearance.

## Battery

| Dimension | Value | Notes |
|---|---|---|
| Model | 503450 LiPo | 1000mAh, 3.7V |
| Size | 34.0 x 50.0 x 5.0 | Portrait orientation in case |
| Cable | Exits right side, routes toward bottom | JST-PH 2-pin |
| Position | Upper portion, behind PCB | Centered XY |
| Position Z | 8.6 to 13.6 | Between PCB and back wall |

## Buttons (Front Face)

Elongated hexagon shape (`<=>`) with rounded corners. 3 buttons only (wake removed).

### Main 3 Buttons (Approve, Action, Reject)

| Dimension | Value |
|---|---|
| Hex width (tip to tip) | 12.0 |
| Hex height (flat to flat) | 6.0 |
| Corner rounding | 1.2 |
| Spacing (center to center) | 14.0 |
| Y position (center) | 43.9 |
| X positions | 16.0, 30.0, 44.0 (centered) |
| Bezel slope margin | 0.5 |
| Bezel slope depth | 0.3 |

### Button Caps

| Dimension | Value | Notes |
|---|---|---|
| Cap clearance | 0.3 per side | Gap between cap and hole |
| Cap top thickness | 1.8 | Visible part |
| Cap protrusion | 0.8 | Above case surface |
| Retention lip | +0.8 per side | Wider than hole to retain |
| Lip thickness | 0.8 | Behind front wall |
| Actuator post | 3.0 dia, 2.0 tall | Presses tactile switch |

## USB-C Cutout (Bottom Edge)

| Dimension | Value | Notes |
|---|---|---|
| Connector | HRO TYPE-C-31-M-12 | |
| Hole width | 9.34 | 8.94 + 2 x 0.2 tolerance |
| Hole height | 3.66 | 3.26 + 2 x 0.2 tolerance |
| Shape | Pill (rounded rectangle) | |
| Position | Centered X, bottom wall | |

## LED Hole

| Dimension | Value |
|---|---|
| Diameter | 2.0 |
| Position | X = 8.0, Y = 55.0 (bottom-left area) |

## Back Cover

| Dimension | Value | Notes |
|---|---|---|
| Plate thickness | 1.5 | Matches wall thickness |
| Outer chamfer | 1.0 | Rounded outer edge |
| Rim height | 2.0 | Inserts into front shell |
| Rim clearance | 0.3 | Gap for snap fit |
| Rim wall thickness | 1.0 | |

### Snap-Fit Clips (4 total on rim)

| Dimension | Value |
|---|---|
| Clip width | 8.0 |
| Clip height | 2.0 |
| Hook overhang | 0.5 |
| Positions | Left, Right (Y centered), Top, Bottom (X centered) |

### PCB Mounting Standoffs (3 on back cover)

| Dimension | Value | Notes |
|---|---|---|
| Outer diameter | 4.0 | |
| Screw hole | 2.2 (M2) | |
| Inset from PCB edge | 3.0 | |
| Height | 5.5 | From back inner wall to PCB solder side |
| Positions | TR, BL, BR corners | TL removed for FPC connector |

### Battery Guide Rails (on back cover)

| Dimension | Value | Notes |
|---|---|---|
| Guide wall thickness | 1.2 | |
| Positions | Left, Right, Top, Bottom (split) | |
| Bottom split gap | 8.0 | For JST cable |
| Height | Back inner wall to Z_BATT | Connects to back wall |

### Motor Pocket (on back cover inner face)

| Dimension | Value |
|---|---|
| Diameter | 6.4 (motor 6.0 + tolerance) |
| Depth | 1.0 |
| Position | X = 25%, Y = 20% of case |

## FDM Print Notes

- Front shell prints face-down (chamfered front on bed)
- Back cover prints outer-face-down (flat back on bed, features up)
- Button caps print top-face-down (visible surface gets bed finish)
- Tolerance: 0.2mm per side for FDM
- No overhangs > 45 degrees
- Display clips are 1.5mm bridges (acceptable for FDM)
