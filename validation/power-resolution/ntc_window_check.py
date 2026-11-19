"""Arithmetic-only voltage-ratio check for a rejected NTC candidate.

Network: VBUS -- RTOP -- SENSE -- NTC -- PACK-.
TLV1702 compares the ratiometric SENSE node to cold and hot divider references.
MCP73871 THERM is intentionally isolated from this network (fixed 10k to VSS).

WARNING: This script does not model comparator output polarity, CE truth table,
startup, feedback state, NTC wiring faults, or charger behavior. It cannot
prove a temperature window or that charging stops. The candidate is rejected
and must not be used for schematic release.
"""
from __future__ import annotations

from math import exp

R25 = 10_000.0
BETA = 4_250.0
TOL_R25 = 0.01
TOL_BETA = 0.01
TOL_FIXED = 0.01

# DS20002090F: ITHERM 47/50/53 uA; VT1 1.20/1.24/1.26 V;
# VT2 0.23/0.25/0.27 V.
I_MIN, I_TYP, I_MAX = 47e-6, 50e-6, 53e-6
VT1_MIN, VT1_TYP, VT1_MAX = 1.20, 1.24, 1.26
VT2_MIN, VT2_TYP, VT2_MAX = 0.23, 0.25, 0.27

# Rejected external-divider arithmetic only. THERM was isolated with a
# fixed resistor. These calculations do not prove the CE gate or faults.
RTOP = 10_000.0
RCOLD_TOP, RCOLD_BOT = 10_000.0, 30_100.0
RHOT_TOP, RHOT_BOT = 22_600.0, 10_000.0
RFB = 1_000_000.0
VOS_MAX = 5.5e-3  # TLV1702 max over -40..125 C
VBUS_MIN = 4.75  # USB nominal-voltage lower bound used for VOS normalization


def ntc(temp_c: float, r25: float, beta: float) -> float:
    return r25 * exp(beta * (1.0 / (temp_c + 273.15) - 1.0 / 298.15))


def ratio(rtop: float, rbottom: float) -> float:
    return rbottom / (rtop + rbottom)


def ntc_node_ratio(rtop: float, rn: float) -> float:
    return rn / (rtop + rn)


def r_corner(temp_c: float, high: bool) -> float:
    # Below 25 C, larger beta makes larger R; above 25 C it makes smaller R.
    beta_high_gives_r_high = temp_c < 25.0
    beta = BETA * (1 + TOL_BETA if high == beta_high_gives_r_high else 1 - TOL_BETA)
    return ntc(temp_c, R25 * (1 + TOL_R25 if high else 1 - TOL_R25), beta)


def node_corner(temp_c: float, high: bool) -> float:
    # Higher node voltage has higher NTC R and lower Rtop.
    return ntc_node_ratio(RTOP * (1 - TOL_FIXED if high else 1 + TOL_FIXED),
                          r_corner(temp_c, high))


def parallel(a: float, b: float) -> float:
    return a * b / (a + b)


def ref_corner(top: float, bottom: float, high: bool, output_high: bool) -> float:
    # Higher divider ratio has high bottom and low top resistance.
    top = top * (1 - TOL_FIXED if high else 1 + TOL_FIXED)
    bottom = bottom * (1 + TOL_FIXED if high else 1 - TOL_FIXED)
    fb = RFB * (1 - TOL_FIXED if high else 1 + TOL_FIXED)
    if output_high:
        top = parallel(top, fb)
    else:
        bottom = parallel(bottom, fb)
    return ratio(top, bottom)


def nominal_trip(target_ratio: float) -> float:
    lo, hi = -20.0, 80.0
    for _ in range(100):
        mid = (lo + hi) / 2
        if ntc_node_ratio(RTOP, ntc(mid, R25, BETA)) > target_ratio:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main() -> None:
    cold_ref = ratio(parallel(RCOLD_TOP, RFB), RCOLD_BOT)
    hot_ref = ratio(parallel(RHOT_TOP, RFB), RHOT_BOT)
    print("WARNING: arithmetic-only check of a rejected candidate; not a CE or safety proof.")
    print(f"NTC=10k B={BETA:.0f} K; RTOP={RTOP:.0f} ohm")
    print("0 C voltage-ratio comparison:",
          f"node_min={node_corner(0, False):.6f}, ",
          f"ref_max+VOS={ref_corner(RCOLD_TOP, RCOLD_BOT, True, True)+VOS_MAX/VBUS_MIN:.6f}")
    print("45 C voltage-ratio comparison:",
          f"node_max={node_corner(45, True):.6f}, ",
          f"ref_min-VOS={ref_corner(RHOT_TOP, RHOT_BOT, False, True)-VOS_MAX/VBUS_MIN:.6f}")
    print(f"candidate nominal cold crossing: {nominal_trip(cold_ref):.2f} C")
    print(f"candidate nominal hot crossing: {nominal_trip(hot_ref):.2f} C")
    for temp in (0, 3, 42, 45):
        print(f"{temp:>2} C: Rntc nominal={ntc(temp, R25, BETA):.1f} ohm, "
              f"Vnode/VBUS min/max={node_corner(temp, False):.5f}/{node_corner(temp, True):.5f}")


if __name__ == "__main__":
    main()
