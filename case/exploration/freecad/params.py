# Devotchi Case — Shared Parameters
# All dimensions in mm

# ──────────────────────────────────
# 3D Print
# ──────────────────────────────────
TOL = 0.2           # FDM printing tolerance per side
WALL = 1.5          # wall thickness
CORNER_R = 3.0      # outer corner radius (XY plane)
CHAMFER = 2.5       # 45-degree edge chamfer on Z edges

# ──────────────────────────────────
# Display (HS20HS072RX 2.0" TFT LCD)
# ──────────────────────────────────
DISP_MOD_W = 51.8   # display module width
DISP_MOD_H = 36.2   # display module height
DISP_MOD_D = 2.5    # display module depth/thickness
DISP_ACT_W = 40.8   # active area width
DISP_ACT_H = 30.6   # active area height
DISP_BEZEL = 1.0    # lip that holds display in window
DISP_FPC_W = 6.5    # FPC tail width (integrated in display)
DISP_FPC_L = 12.1   # FPC tail length from module edge

# ──────────────────────────────────
# PCB
# ──────────────────────────────────
PCB_W = 45.0        # PCB width
PCB_H = 50.0        # PCB height (extended for FPC connector clearance)
PCB_D = 1.6         # PCB thickness

# ──────────────────────────────────
# Battery (503450 LiPo, 1000mAh)
# ──────────────────────────────────
BATT_W = 34.0       # battery width (portrait orientation)
BATT_H = 50.0       # battery height (portrait, cable exits right side toward bottom)
BATT_D = 5.0        # battery thickness

# ──────────────────────────────────
# Case outer dimensions (60 x 60 — clean numbers)
# ──────────────────────────────────
CASE_W = 60.0       # case width (fixed)
CASE_H = 60.0       # case height (fixed)

# Derived clearances from fixed case size
DISP_CLEARANCE = CASE_W - DISP_MOD_W - 2 * WALL - 2 * TOL  # 4.8mm total

# Height zones (front view, top to bottom)
CASE_H_DISPLAY = DISP_MOD_H + 2 * WALL                      # 39.2mm
CASE_H_USB = 5.0                                             # USB area at bottom
CASE_H_BUTTONS = CASE_H - CASE_H_DISPLAY - CASE_H_USB       # 15.8mm

# ──────────────────────────────────
# Depth stack (front to back)
# ──────────────────────────────────
GAP_DISP_PCB = 2.5   # gap for ESP32 (2.4mm module + 0.1mm clearance)
GAP_PCB_BATT = 5.0   # gap behind PCB solder-side (JST connector 4.8mm + clearance)

# Depth stack (front to back):
# wall(1.5) + display(2.5) + gap(2.5) + PCB(1.6) + gap(0.5) + battery(5.0) + wall(1.5) = 15.1
CASE_D = WALL + DISP_MOD_D + GAP_DISP_PCB + PCB_D + 0.5 + BATT_D + WALL  # 15.1mm

# Z positions (from front face = 0, going inward / +Z)
Z_DISP = WALL                                     # 1.5
Z_PCB = WALL + DISP_MOD_D + GAP_DISP_PCB          # 6.5
Z_BATT = Z_PCB + PCB_D + 0.5                      # 8.6

# Front shell depth (everything except back cover wall)
SHELL_D = CASE_D - WALL  # 13.6mm

# ──────────────────────────────────
# PCB positioning in case
# ──────────────────────────────────
PCB_OFFSET_X = (CASE_W - PCB_W) / 2              # 7.5mm — centered horizontally
PCB_OFFSET_Y = CASE_H - WALL - PCB_H             # 8.5mm — bottom-aligned for USB-C

# ──────────────────────────────────
# Buttons (4 front, no side button)
# ──────────────────────────────────
BTN_HEX_W = 12.0     # elongated hex width (tip to tip)
BTN_HEX_H = 6.0      # elongated hex height (flat to flat)
BTN_HEX_CORNER_R = 1.2  # rounding on hex corners
WAKE_HEX_W = 10.0    # wake button: slightly narrower
WAKE_HEX_H = 4.5     # wake button: shorter to avoid USB zone
BTN_CAP_CLEARANCE = 0.3
BTN_CAP_TRAVEL = 0.8      # how far cap protrudes above case surface
BTN_SPACING = 14.0   # center-to-center for main 3

# Main 3 buttons Y position (in button zone)
BTN_Y = CASE_H_DISPLAY + CASE_H_BUTTONS * 0.30   # ~43.9mm
# Wake button Y position (further below main 3)
BTN_WAKE_Y = CASE_H_DISPLAY + CASE_H_BUTTONS * 0.80  # ~51.8mm

# X positions (centered)
BTN_X_APPROVE = CASE_W / 2 - BTN_SPACING          # 16.0mm
BTN_X_ACTION = CASE_W / 2                          # 30.0mm
BTN_X_REJECT = CASE_W / 2 + BTN_SPACING            # 44.0mm
BTN_X_WAKE = CASE_W / 2                            # 30.0mm

# ──────────────────────────────────
# USB-C (HRO TYPE-C-31-M-12)
# ──────────────────────────────────
USBC_W = 8.94 + 2 * TOL   # connector width + tolerance
USBC_H = 3.26 + 2 * TOL   # connector height + tolerance (full shell height)
USBC_R = 0.8               # corner rounding for snug fit
USBC_OVERHANG = 1.95       # connector protrudes past PCB edge

# ──────────────────────────────────
# LED hole (front face, bottom-left)
# ──────────────────────────────────
LED_HOLE_D = 2.0
LED_X = 8.0
LED_Y = CASE_H - 5.0       # 55.0mm

# ──────────────────────────────────
# Motor (6mm coin vibration)
# ──────────────────────────────────
MOTOR_D = 6.0
MOTOR_H = 2.1

# ──────────────────────────────────
# PCB mounting posts
# ──────────────────────────────────
POST_OD = 4.0        # outer diameter of standoff
POST_ID = 2.2        # M2 screw hole (2.0mm + tolerance)
POST_INSET = 3.0     # inset from PCB edge (3 holes: TR, BL, BR — TL removed for FPC)
POST_H = DISP_MOD_D + GAP_DISP_PCB  # 5.0mm (from front inner wall to PCB)

# ──────────────────────────────────
# Snap-fit
# ──────────────────────────────────
SNAP_W = 8.0         # clip width
SNAP_H = 2.0         # clip height
SNAP_OVERHANG = 0.5  # hook depth
SNAP_GAP = 0.3       # clearance for flex

# ──────────────────────────────────
# FPC cable slot
# ──────────────────────────────────
FPC_SLOT_W = DISP_FPC_W + 2.0   # 8.5mm with clearance
FPC_SLOT_H = 2.0

# ──────────────────────────────────
# Back cover
# ──────────────────────────────────
COVER_WALL = WALL
RIM_H = 2.0          # how deep rim inserts into front shell
RIM_CLEARANCE = 0.3  # gap for fit
RIM_WALL = 1.0       # rim wall thickness

# ──────────────────────────────────
# Button caps
# ──────────────────────────────────
CAP_HEX_W = BTN_HEX_W - 2 * BTN_CAP_CLEARANCE  # cap width (smaller than hole)
CAP_HEX_H = BTN_HEX_H - 2 * BTN_CAP_CLEARANCE  # cap height
CAP_TOP_D = 1.8      # visible top thickness (sits above case surface)
CAP_LIP_EXTRA = 0.8  # lip extends this far past hole edge on EACH side
CAP_LIP_D = 0.8      # lip thickness
CAP_POST_D = 3.0     # actuator post diameter
CAP_POST_H = 2.0     # actuator post height (reaches switch)
