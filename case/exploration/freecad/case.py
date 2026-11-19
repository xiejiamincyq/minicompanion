#!/usr/bin/env python3
"""Devotchi Case — FreeCAD Python parametric design.

Run headless:
    flatpak run --command=FreeCADCmd org.freecad.FreeCAD case.py
"""
import sys
import os
import math

# Add this directory to path for params import
try:
    _dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _dir = os.getcwd()
sys.path.insert(0, _dir)
from params import *

import FreeCAD
import Part
import MeshPart

# Create a document (needed for some operations)
doc = FreeCAD.newDocument("Devotchi")

# ──────────────────────────────────────────────
# Helper: 2D rounded rectangle
# ──────────────────────────────────────────────

def rounded_rect_wire(w, h, r):
    """Create a 2D rounded-rectangle wire in XY plane at Z=0.
    Origin at (0, 0) — bottom-left corner of bounding box.
    """
    r = min(r, w / 2, h / 2)
    cx = [r, w - r, w - r, r]
    cy = [r, r, h - r, h - r]
    angles = [180, 270, 0, 90]

    edges = []
    for i in range(4):
        a_start = math.radians(angles[i])
        a_mid = math.radians(angles[i] + 45)
        a_end = math.radians(angles[i] + 90)
        p1 = FreeCAD.Vector(cx[i] + r * math.cos(a_start),
                            cy[i] + r * math.sin(a_start), 0)
        pm = FreeCAD.Vector(cx[i] + r * math.cos(a_mid),
                            cy[i] + r * math.sin(a_mid), 0)
        p2 = FreeCAD.Vector(cx[i] + r * math.cos(a_end),
                            cy[i] + r * math.sin(a_end), 0)
        edges.append(Part.Arc(p1, pm, p2).toShape())

        j = (i + 1) % 4
        a_next_start = math.radians(angles[j])
        p_next = FreeCAD.Vector(cx[j] + r * math.cos(a_next_start),
                                cy[j] + r * math.sin(a_next_start), 0)
        edges.append(Part.LineSegment(p2, p_next).toShape())

    return Part.Wire(edges)


def rounded_rect_face(w, h, r):
    wire = rounded_rect_wire(w, h, r)
    return Part.Face(wire)


def rounded_box(w, h, d, r):
    face = rounded_rect_face(w, h, r)
    return face.extrude(FreeCAD.Vector(0, 0, d))


# ──────────────────────────────────────────────
# Helper: chamfered box via loft
# ──────────────────────────────────────────────

def chamfered_box(w, h, d, r, chamf, front_only=False):
    """Box with 45-degree chamfered Z-edges via loft.
    If front_only=True, only chamfer the Z=0 (front) face.
    The Z=d (back) face stays full-size for a flush back cover.
    """
    chamf = min(chamf, d / 2 - 0.1)
    r_inner = max(r - chamf, 0.5)
    w0 = w - 2 * chamf
    h0 = h - 2 * chamf

    # Front face: inset by chamf
    wire0 = rounded_rect_wire(w0, h0, r_inner)
    wire0.translate(FreeCAD.Vector(chamf, chamf, 0))
    # Full size at Z=chamf
    wire1 = rounded_rect_wire(w, h, r)
    wire1.translate(FreeCAD.Vector(0, 0, chamf))

    if front_only:
        # Back face: full size (no chamfer)
        wire2 = rounded_rect_wire(w, h, r)
        wire2.translate(FreeCAD.Vector(0, 0, d))
        return Part.makeLoft([wire0, wire1, wire2], True)
    else:
        wire2 = rounded_rect_wire(w, h, r)
        wire2.translate(FreeCAD.Vector(0, 0, d - chamf))
        wire3 = rounded_rect_wire(w0, h0, r_inner)
        wire3.translate(FreeCAD.Vector(chamf, chamf, d))
        return Part.makeLoft([wire0, wire1, wire2, wire3], True)


# ──────────────────────────────────────────────
# Helper: pill (stadium) shape
# ──────────────────────────────────────────────

def pill_wire(w, h):
    """Stadium/pill-shaped wire centered at origin in XY plane."""
    r = h / 2
    hw = w / 2 - r

    edges = []
    p1 = FreeCAD.Vector(hw, r, 0)
    pm_r = FreeCAD.Vector(hw + r, 0, 0)
    p2 = FreeCAD.Vector(hw, -r, 0)
    edges.append(Part.Arc(p1, pm_r, p2).toShape())
    p3 = FreeCAD.Vector(-hw, -r, 0)
    edges.append(Part.LineSegment(p2, p3).toShape())
    pm_l = FreeCAD.Vector(-hw - r, 0, 0)
    p4 = FreeCAD.Vector(-hw, r, 0)
    edges.append(Part.Arc(p3, pm_l, p4).toShape())
    edges.append(Part.LineSegment(p4, p1).toShape())

    return Part.Wire(edges)


def pill_solid(w, h, depth):
    """Extruded pill shape centered at origin, extends in +Z."""
    face = Part.Face(pill_wire(w, h))
    return face.extrude(FreeCAD.Vector(0, 0, depth))


# ──────────────────────────────────────────────
# Helper: rounded hexagon
# ──────────────────────────────────────────────

def elongated_hex_wire(w, h, corner_r=0):
    """Elongated hexagon wire centered at origin (like <=> shape).
    w: total width (tip to tip, horizontal)
    h: total height (flat to flat, vertical)
    corner_r: rounding radius on each corner.
    Vertices: left tip (-w/2, 0), right tip (w/2, 0),
    and 4 middle vertices at (+-w/4, +-h/2).
    """
    cr = min(corner_r, h / 4, w / 8)

    # 6 vertices: right tip, upper-right, upper-left, left tip, lower-left, lower-right
    verts = [
        (w / 2, 0),           # right tip
        (w / 4, h / 2),       # upper right
        (-w / 4, h / 2),      # upper left
        (-w / 2, 0),          # left tip
        (-w / 4, -h / 2),     # lower left
        (w / 4, -h / 2),      # lower right
    ]

    if cr < 0.01:
        edges = []
        for i in range(6):
            j = (i + 1) % 6
            p1 = FreeCAD.Vector(verts[i][0], verts[i][1], 0)
            p2 = FreeCAD.Vector(verts[j][0], verts[j][1], 0)
            edges.append(Part.LineSegment(p1, p2).toShape())
        return Part.Wire(edges)

    # Build with rounded corners
    arcs = []
    for i in range(6):
        i_prev = (i - 1) % 6
        i_next = (i + 1) % 6
        vx, vy = verts[i]
        px, py = verts[i_prev]
        nx, ny = verts[i_next]

        # Unit vectors from vertex to neighbors
        dp = math.hypot(px - vx, py - vy)
        dn = math.hypot(nx - vx, ny - vy)
        upx, upy = (px - vx) / dp, (py - vy) / dp
        unx, uny = (nx - vx) / dn, (ny - vy) / dn

        # Arc endpoints (inset from vertex along edges)
        arc_start = FreeCAD.Vector(vx + upx * cr, vy + upy * cr, 0)
        arc_end = FreeCAD.Vector(vx + unx * cr, vy + uny * cr, 0)

        # Arc midpoint: compute from fillet geometry
        # Bisector direction (pointing inward from vertex)
        bx = (upx + unx) / 2
        by = (upy + uny) / 2
        bl = math.hypot(bx, by)
        if bl > 0.001:
            bx /= bl
            by /= bl
        # Distance from vertex to arc center along bisector
        dot = upx * unx + upy * uny
        half_angle = math.acos(max(-1.0, min(1.0, dot))) / 2
        if half_angle > 0.001:
            center_dist = cr / math.sin(half_angle)
        else:
            center_dist = cr
        # Arc midpoint is on the fillet circle, on the bisector
        arc_mid_dist = center_dist - cr
        arc_mid = FreeCAD.Vector(vx + bx * arc_mid_dist,
                                  vy + by * arc_mid_dist, 0)

        arcs.append(Part.Arc(arc_start, arc_mid, arc_end).toShape())

    # Assemble: arc, line, arc, line, ...
    all_edges = []
    for i in range(6):
        all_edges.append(arcs[i])
        next_arc = arcs[(i + 1) % 6]
        line = Part.LineSegment(
            arcs[i].Vertexes[-1].Point,
            next_arc.Vertexes[0].Point
        ).toShape()
        all_edges.append(line)

    return Part.Wire(all_edges)


def elongated_hex_solid(w, h, corner_r, depth):
    """Extruded elongated hexagon centered at origin, extends in +Z."""
    face = Part.Face(elongated_hex_wire(w, h, corner_r))
    return face.extrude(FreeCAD.Vector(0, 0, depth))


# ──────────────────────────────────────────────
# Front Shell
# ──────────────────────────────────────────────

def build_front_shell():
    """Front shell: display pocket + button holes + USB-C cutout.
    PCB standoffs grow from front inner wall to Z_PCB.
    Display held by pocket + retention clips.
    No battery guides here — those are on the back cover.
    """
    print("  Building outer shell...")
    shell = chamfered_box(CASE_W, CASE_H, SHELL_D, CORNER_R, CHAMFER, front_only=True)

    cuts = []

    # 1. Interior cavity
    inner_r = max(CORNER_R - WALL, 0.5)
    cavity = rounded_box(CASE_W - 2 * WALL, CASE_H - 2 * WALL, SHELL_D, inner_r)
    cavity.translate(FreeCAD.Vector(WALL, WALL, WALL))
    cuts.append(cavity)

    # 2. Display window with sloped bezel
    #    At Z=0 (front face): larger opening with slope margin
    #    At Z=slope_depth: exact window size (active area)
    #    From Z=slope_depth to Z=WALL: straight through at window size
    slope_margin = 1.5   # how far slope extends beyond window edge
    slope_depth = 0.8    # how deep the slope goes into front wall

    disp_win_x = (CASE_W - DISP_ACT_W) / 2
    disp_win_y = WALL + (CASE_H_DISPLAY - 2 * WALL - DISP_ACT_H) / 2

    # Sloped bezel: loft from larger rect at Z=0 to window rect at Z=slope_depth
    outer_w = DISP_ACT_W + 2 * slope_margin
    outer_h = DISP_ACT_H + 2 * slope_margin
    outer_x = disp_win_x - slope_margin
    outer_y = disp_win_y - slope_margin

    wire_top = rounded_rect_wire(outer_w, outer_h, 1.5)
    wire_top.translate(FreeCAD.Vector(outer_x, outer_y, -0.1))
    wire_bot = rounded_rect_wire(DISP_ACT_W, DISP_ACT_H, 0.5)
    wire_bot.translate(FreeCAD.Vector(disp_win_x, disp_win_y, slope_depth))
    bezel_cut = Part.makeLoft([wire_top, wire_bot], True)
    cuts.append(bezel_cut)

    # Straight window hole from slope_depth through rest of front wall
    win = Part.makeBox(DISP_ACT_W, DISP_ACT_H, WALL - slope_depth + 0.2)
    win.translate(FreeCAD.Vector(disp_win_x, disp_win_y, slope_depth))
    cuts.append(win)

    # 3. Display pocket (seats module behind window)
    #    The pocket starts at Z=WALL (inner wall surface). The display sits
    #    flush with the inner wall — the front wall overlaps the display
    #    edges by ~5.5mm per side (window is 40.8mm, module is 51.8mm).
    #    Use full inner cavity width/height so display fits with tolerance.
    pocket_w = CASE_W - 2 * WALL  # full inner width
    pocket_h = CASE_H_DISPLAY - 2 * WALL  # full display zone inner height
    pocket_x = WALL
    pocket_y = WALL
    pocket = Part.makeBox(pocket_w, pocket_h, DISP_MOD_D + 0.5)
    pocket.translate(FreeCAD.Vector(pocket_x, pocket_y, WALL))
    cuts.append(pocket)

    # FPC cable routes through the open interior cavity — no separate slot needed.

    # 4. Elongated hex button holes with subtle sloped bezel
    btn_slope_margin = 0.5   # subtle slope beyond hole edge
    btn_slope_depth = 0.3    # shallow slope

    for (bx, by, bw, bh) in BTN_POSITIONS:
        # Sloped bezel: larger hex at surface, actual size at slope_depth
        wire_top = elongated_hex_wire(bw + 2 * btn_slope_margin,
                                       bh + 2 * btn_slope_margin,
                                       BTN_HEX_CORNER_R + 0.3)
        wire_top.translate(FreeCAD.Vector(bx, by, -0.1))
        wire_bot = elongated_hex_wire(bw, bh, BTN_HEX_CORNER_R)
        wire_bot.translate(FreeCAD.Vector(bx, by, btn_slope_depth))
        bezel = Part.makeLoft([wire_top, wire_bot], True)
        cuts.append(bezel)

        # Straight hex hole through rest of wall
        hole = elongated_hex_solid(bw, bh, BTN_HEX_CORNER_R,
                                    WALL - btn_slope_depth + 0.2)
        hole.translate(FreeCAD.Vector(bx, by, btn_slope_depth))
        cuts.append(hole)

    # 6. USB-C cutout (clean pill hole through bottom wall)
    usbc_center_x = CASE_W / 2
    usbc_center_z = Z_PCB - USBC_H / 2
    usbc_pill = pill_solid(USBC_W, USBC_H, 10.0)
    usbc_pill.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), -90)
    usbc_pill.translate(FreeCAD.Vector(usbc_center_x, CASE_H - 5.0, usbc_center_z))
    cuts.append(usbc_pill)

    # 7. LED hole
    led = Part.makeCylinder(LED_HOLE_D / 2, WALL + 0.2)
    led.translate(FreeCAD.Vector(LED_X, LED_Y, -0.1))
    cuts.append(led)

    # 8. Snap-fit sockets (recesses at back edge of inner walls)
    for (sx, sy, side) in SNAP_SOCKET_POSITIONS:
        if side in ('left', 'right'):
            sock = Part.makeBox(SNAP_OVERHANG + 0.1, SNAP_W, SNAP_H)
        else:
            sock = Part.makeBox(SNAP_W, SNAP_OVERHANG + 0.1, SNAP_H)
        sock.translate(FreeCAD.Vector(sx, sy, SHELL_D - SNAP_H))
        cuts.append(sock)

    # Apply cuts one at a time (compound fuse can fail with complex lofts)
    print("  Applying %d cuts..." % len(cuts))
    for i, cut in enumerate(cuts):
        try:
            shell = shell.cut(cut)
        except Exception as e:
            print(f"  WARNING: cut {i} failed: {e}")

    # ── Additive features ──

    # 9. Display retention clips (left, right, top)
    clip_len = 8.0
    clip_ovlp = 1.5
    clip_d = 1.0
    disp_z = WALL + DISP_MOD_D - clip_d

    clips = []
    # FPC exits left edge at ~15.3mm from top, ~3.5mm tall.
    # All clips are thin lips at display back depth. The 1.5mm overhang
    # is short enough for FDM without support.
    fpc_y_on_disp = 15.3
    fpc_zone = 5.0
    side_clip_len = 5.0

    # Left clips (2x, avoiding FPC zone)
    c = Part.makeBox(clip_ovlp, side_clip_len, clip_d)
    c.translate(FreeCAD.Vector(pocket_x, pocket_y + 1.0, disp_z))
    clips.append(c)
    c = Part.makeBox(clip_ovlp, side_clip_len, clip_d)
    c.translate(FreeCAD.Vector(pocket_x, pocket_y + fpc_y_on_disp + fpc_zone, disp_z))
    clips.append(c)
    # Right clips (2x, matching)
    c = Part.makeBox(clip_ovlp, side_clip_len, clip_d)
    c.translate(FreeCAD.Vector(pocket_x + pocket_w - clip_ovlp, pocket_y + 1.0, disp_z))
    clips.append(c)
    c = Part.makeBox(clip_ovlp, side_clip_len, clip_d)
    c.translate(FreeCAD.Vector(pocket_x + pocket_w - clip_ovlp,
                               pocket_y + fpc_y_on_disp + fpc_zone, disp_z))
    clips.append(c)
    # Top clip
    c = Part.makeBox(clip_len, clip_ovlp, clip_d)
    c.translate(FreeCAD.Vector(pocket_x + (pocket_w - clip_len) / 2,
                               pocket_y, disp_z))
    clips.append(c)

    print("  Applying additions...")
    for clip in clips:
        shell = shell.fuse(clip)

    return shell


# ──────────────────────────────────────────────
# Back Cover (built in assembly position)
# ──────────────────────────────────────────────

def build_back_cover():
    """Back cover built in its final assembly position.
    Outer face at Z=CASE_D, inner face at Z=CASE_D-COVER_WALL.
    Rim extends inward (-Z).
    Battery guides and PCB support ledges grow inward from inner face.
    """
    z_outer = CASE_D           # outer face
    z_inner = CASE_D - COVER_WALL  # inner face

    # 1. Back plate with rounded/chamfered outer edge
    #    Inner face (z_inner) is full-size to mate with front shell.
    #    Outer face (z_outer) is inset with chamfer for rounded look.
    back_chamf = 1.0  # chamfer on outer edge
    r_chamf = max(CORNER_R - back_chamf, 0.5)
    w_chamf = CASE_W - 2 * back_chamf
    h_chamf = CASE_H - 2 * back_chamf

    wire0 = rounded_rect_wire(CASE_W, CASE_H, CORNER_R)
    wire0.translate(FreeCAD.Vector(0, 0, z_inner))
    wire1 = rounded_rect_wire(CASE_W, CASE_H, CORNER_R)
    wire1.translate(FreeCAD.Vector(0, 0, z_outer - back_chamf))
    wire2 = rounded_rect_wire(w_chamf, h_chamf, r_chamf)
    wire2.translate(FreeCAD.Vector(back_chamf, back_chamf, z_outer))

    plate = Part.makeLoft([wire0, wire1, wire2], True)

    # 2. Inner rim (inserts into front shell, extends toward front)
    rim_w = CASE_W - 2 * WALL - 2 * RIM_CLEARANCE
    rim_h = CASE_H - 2 * WALL - 2 * RIM_CLEARANCE
    rim_r = max(CORNER_R - WALL, 0.5)
    rim_outer = rounded_box(rim_w, rim_h, RIM_H, rim_r)
    rim_inner = rounded_box(rim_w - 2 * RIM_WALL, rim_h - 2 * RIM_WALL,
                            RIM_H + 0.1, max(rim_r - RIM_WALL, 0.3))
    rim_inner.translate(FreeCAD.Vector(RIM_WALL, RIM_WALL, -0.05))
    rim = rim_outer.cut(rim_inner)
    # Rim extends from inner face toward front (in -Z direction)
    rim.translate(FreeCAD.Vector(WALL + RIM_CLEARANCE,
                                 WALL + RIM_CLEARANCE,
                                 z_inner - RIM_H))
    plate = plate.fuse(rim)

    # 3. Snap-fit clips (on rim outer faces)
    clip_configs = [
        # Left wall
        (WALL + RIM_CLEARANCE - SNAP_OVERHANG,
         CASE_H / 2 - SNAP_W / 2, 'x', SNAP_W),
        # Right wall
        (CASE_W - WALL - RIM_CLEARANCE,
         CASE_H / 2 - SNAP_W / 2, 'x', SNAP_W),
        # Top wall
        (CASE_W / 2 - SNAP_W / 2,
         WALL + RIM_CLEARANCE - SNAP_OVERHANG, 'y', SNAP_W),
        # Bottom wall
        (CASE_W / 2 - SNAP_W / 2,
         CASE_H - WALL - RIM_CLEARANCE, 'y', SNAP_W),
    ]
    for (cx, cy, direction, length) in clip_configs:
        if direction == 'x':
            clip = Part.makeBox(SNAP_OVERHANG, length, SNAP_H)
        else:
            clip = Part.makeBox(length, SNAP_OVERHANG, SNAP_H)
        clip.translate(FreeCAD.Vector(cx, cy, z_inner - RIM_H))
        plate = plate.fuse(clip)

    # 4. Battery guide rails (grow from inner face toward front)
    #    These hold the battery in place between Z_BATT and Z_BATT+BATT_D
    batt_x = (CASE_W - BATT_W) / 2
    batt_y = (CASE_H_DISPLAY - BATT_H) / 2  # battery in display zone
    guide_w = 1.2
    margin = 5.0
    # Guides extend from inner face down to battery bottom
    guide_z_start = Z_BATT
    guide_z_height = z_inner - Z_BATT  # fills gap from battery to back wall

    # Left guide
    g = Part.makeBox(guide_w, BATT_H - 2 * margin, guide_z_height)
    g.translate(FreeCAD.Vector(batt_x - guide_w, batt_y + margin, guide_z_start))
    plate = plate.fuse(g)
    # Right guide
    g = Part.makeBox(guide_w, BATT_H - 2 * margin, guide_z_height)
    g.translate(FreeCAD.Vector(batt_x + BATT_W, batt_y + margin, guide_z_start))
    plate = plate.fuse(g)
    # Top guide
    g = Part.makeBox(BATT_W - 2 * margin, guide_w, guide_z_height)
    g.translate(FreeCAD.Vector(batt_x + margin, batt_y - guide_w, guide_z_start))
    plate = plate.fuse(g)
    # Bottom guide (split for JST cable)
    notch_w = 8.0
    half = (BATT_W - 2 * margin - notch_w) / 2
    g = Part.makeBox(half, guide_w, guide_z_height)
    g.translate(FreeCAD.Vector(batt_x + margin, batt_y + BATT_H, guide_z_start))
    plate = plate.fuse(g)
    g = Part.makeBox(half, guide_w, guide_z_height)
    g.translate(FreeCAD.Vector(batt_x + BATT_W - margin - half,
                               batt_y + BATT_H, guide_z_start))
    plate = plate.fuse(g)

    # 5. PCB mounting standoffs (cylindrical, with M2 screw holes)
    #    Grow from back cover inner face toward the PCB solder side.
    #    PCB screws in from the front (component side) through the PCB holes
    #    into these standoffs.
    pcb_standoff_h = z_inner - (Z_PCB + PCB_D)  # gap from PCB back to inner wall
    for (px, py) in PCB_POST_POSITIONS:
        post = Part.makeCylinder(POST_OD / 2, pcb_standoff_h)
        post.translate(FreeCAD.Vector(px, py, Z_PCB + PCB_D))
        # M2 screw hole (screws come from PCB front side, through PCB, into standoff)
        hole = Part.makeCylinder(POST_ID / 2, pcb_standoff_h + 0.2)
        hole.translate(FreeCAD.Vector(px, py, Z_PCB + PCB_D - 0.1))
        post = post.cut(hole)
        plate = plate.fuse(post)

    # 6. Motor pocket (recess on inner face)
    motor_pocket = Part.makeCylinder(MOTOR_D / 2 + TOL, 1.0)
    motor_x = CASE_W * 0.25
    motor_y = CASE_H * 0.2
    motor_pocket.translate(FreeCAD.Vector(motor_x, motor_y, z_inner))
    plate = plate.cut(motor_pocket)

    return plate


# ──────────────────────────────────────────────
# Button Caps
# ──────────────────────────────────────────────

def build_button_cap_sized(w, h):
    """Elongated hex button cap with given dimensions."""
    cap_w = w - 2 * BTN_CAP_CLEARANCE
    cap_h = h - 2 * BTN_CAP_CLEARANCE
    top = elongated_hex_solid(cap_w, cap_h, BTN_HEX_CORNER_R, CAP_TOP_D)
    lip = elongated_hex_solid(cap_w + 2 * CAP_LIP_EXTRA,
                               cap_h + 2 * CAP_LIP_EXTRA,
                               BTN_HEX_CORNER_R, CAP_LIP_D)
    lip.translate(FreeCAD.Vector(0, 0, CAP_TOP_D))
    post = Part.makeCylinder(CAP_POST_D / 2, CAP_POST_H)
    post.translate(FreeCAD.Vector(0, 0, CAP_TOP_D + CAP_LIP_D))
    return top.fuse(lip).fuse(post)


def build_button_caps_print():
    """4 button caps in a row for batch printing (STL export)."""
    caps = None
    x_offset = 0
    for (_, _, bw, bh) in BTN_POSITIONS:
        cap = build_button_cap_sized(bw, bh)
        cap.translate(FreeCAD.Vector(x_offset, 0, 0))
        if caps is None:
            caps = cap
        else:
            caps = caps.fuse(cap)
        x_offset += bw + 3.0
    return caps


def build_button_caps_assembly():
    """4 button caps positioned in their case locations."""
    caps = None
    for (bx, by, bw, bh) in BTN_POSITIONS:
        cap = build_button_cap_sized(bw, bh)
        cap.translate(FreeCAD.Vector(bx, by, -BTN_CAP_TRAVEL))
        if caps is None:
            caps = cap
        else:
            caps = caps.fuse(cap)
    return caps


# ──────────────────────────────────────────────
# Ghost components (assembly visualization)
# ──────────────────────────────────────────────

def build_ghost_display():
    disp = Part.makeBox(DISP_MOD_W, DISP_MOD_H, DISP_MOD_D)
    disp_x = (CASE_W - DISP_MOD_W) / 2
    disp_y = WALL + (CASE_H_DISPLAY - 2 * WALL - DISP_MOD_H) / 2
    disp.translate(FreeCAD.Vector(disp_x, disp_y, Z_DISP))
    return disp


def build_ghost_pcb():
    pcb = Part.makeBox(PCB_W, PCB_H, PCB_D)
    pcb.translate(FreeCAD.Vector(PCB_OFFSET_X, PCB_OFFSET_Y, Z_PCB))
    return pcb


def build_ghost_battery():
    batt = Part.makeBox(BATT_W, BATT_H, BATT_D)
    batt_x = (CASE_W - BATT_W) / 2
    batt_y = (CASE_H_DISPLAY - BATT_H) / 2  # battery in display zone
    batt.translate(FreeCAD.Vector(batt_x, batt_y, Z_BATT))
    return batt


# ──────────────────────────────────────────────
# Shared positions (used by multiple builders)
# ──────────────────────────────────────────────

# (x, y, hex_w, hex_h) per button
BTN_POSITIONS = [
    (BTN_X_APPROVE, BTN_Y, BTN_HEX_W, BTN_HEX_H),
    (BTN_X_ACTION, BTN_Y, BTN_HEX_W, BTN_HEX_H),
    (BTN_X_REJECT, BTN_Y, BTN_HEX_W, BTN_HEX_H),
    (BTN_X_WAKE, BTN_WAKE_Y, WAKE_HEX_W, WAKE_HEX_H),
]

PCB_POST_POSITIONS = [
    (PCB_OFFSET_X + POST_INSET, PCB_OFFSET_Y + POST_INSET),
    (PCB_OFFSET_X + PCB_W - POST_INSET, PCB_OFFSET_Y + POST_INSET),
    (PCB_OFFSET_X + POST_INSET, PCB_OFFSET_Y + PCB_H - POST_INSET),
    (PCB_OFFSET_X + PCB_W - POST_INSET, PCB_OFFSET_Y + PCB_H - POST_INSET),
]

SNAP_SOCKET_POSITIONS = [
    (WALL - SNAP_OVERHANG, CASE_H / 2 - SNAP_W / 2, 'left'),
    (CASE_W - WALL, CASE_H / 2 - SNAP_W / 2, 'right'),
    (CASE_W / 2 - SNAP_W / 2, WALL - SNAP_OVERHANG, 'top'),
    (CASE_W / 2 - SNAP_W / 2, CASE_H - WALL, 'bottom'),
]


# ──────────────────────────────────────────────
# Export
# ──────────────────────────────────────────────

def export_stl(shape, filepath):
    mesh = MeshPart.meshFromShape(Shape=shape,
                                  LinearDeflection=0.05,
                                  AngularDeflection=0.5)
    mesh.write(filepath)
    print(f"  Exported: {filepath}")


def export_step(shapes_dict, filepath):
    parts = [shape for shape in shapes_dict.values()]
    compound = Part.makeCompound(parts)
    compound.exportStep(filepath)
    print(f"  Exported: {filepath}")


def add_to_doc(doc, name, shape, color=None, transparency=0):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    try:
        if color and obj.ViewObject:
            obj.ViewObject.ShapeColor = color
        if transparency and obj.ViewObject:
            obj.ViewObject.Transparency = transparency
    except (AttributeError, TypeError):
        pass
    return obj


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    output_dir = _dir

    print("Building front shell...")
    front = build_front_shell()
    export_stl(front, os.path.join(output_dir, "front_shell.stl"))

    print("Building back cover...")
    back = build_back_cover()
    # For STL export: flip so outer face is on print bed (Z=0)
    # Back cover outer face is at Z=CASE_D. Rotate 180 around X axis
    # to flip it, then translate so everything is above Z=0.
    back_print = back.copy()
    # Rotate 180 around X through the center of the part
    center_y = CASE_H / 2
    center_z = CASE_D / 2
    back_print.rotate(FreeCAD.Vector(0, center_y, center_z),
                      FreeCAD.Vector(1, 0, 0), 180)
    # Now outer face is near Z=0, internal features point up
    bb = back_print.BoundBox
    back_print.translate(FreeCAD.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    export_stl(back_print, os.path.join(output_dir, "back_cover.stl"))

    print("Building button caps...")
    caps_print = build_button_caps_print()
    export_stl(caps_print, os.path.join(output_dir, "button_caps.stl"))

    # Assembly visualization
    print("Building assembly...")
    caps_asm = build_button_caps_assembly()

    export_step({
        'front_shell': front,
        'back_cover': back,
        'button_caps': caps_asm,
        'display': build_ghost_display(),
        'pcb': build_ghost_pcb(),
        'battery': build_ghost_battery(),
    }, os.path.join(output_dir, "assembly.step"))

    # Native FreeCAD project
    print("Saving FreeCAD project...")
    add_to_doc(doc, "FrontShell", front, color=(0.35, 0.35, 0.35))
    add_to_doc(doc, "BackCover", back, color=(0.5, 0.5, 0.5))
    add_to_doc(doc, "ButtonCaps", caps_asm, color=(0.9, 0.9, 0.9))
    add_to_doc(doc, "Display", build_ghost_display(),
               color=(0.2, 0.3, 0.3), transparency=60)
    add_to_doc(doc, "PCB", build_ghost_pcb(),
               color=(0.0, 0.5, 0.0), transparency=60)
    add_to_doc(doc, "Battery", build_ghost_battery(),
               color=(0.1, 0.4, 0.9), transparency=60)

    doc.recompute()
    fcstd_path = os.path.join(output_dir, "devotchi_case.FCStd")
    doc.saveAs(fcstd_path)
    print(f"  Saved: {fcstd_path}")

    print("Done!")


_already_ran = globals().get('_already_ran', False)
if not _already_ran:
    _already_ran = True
    main()
