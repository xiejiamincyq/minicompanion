"""Check the service components and access from the rear against exported STEP solids.

Run with the same CadQuery environment as build.py, after generating step/global.
The route envelopes come from the specified part courtyard, actuator travel and
tool clearance. The battery outline is its drawing envelope, not the soft wiring.
"""
import hashlib
import json
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
PARAMS = json.loads((ROOT / "design/parameters.json").read_text(encoding="utf-8"))
PORTS = PARAMS["service_ports"]
PCB_BACK = 8.2062
CASE_TOP = PARAMS["case"]["height"]


def prism(center, size, z_min, z_max):
    x, y = center
    width, height = size
    return cq.Solid.makeBox(width, height, z_max - z_min,
                            cq.Vector(x - width / 2, y - height / 2, z_min))


def run():
    components = {
        "SERVICE": ((8.5, 9.5), 5.65),
        "BOOT": ((7.54, 5.65), 1.70),
    }
    solids = {path.stem: cq.importers.importStep(str(path)).val()
              for path in sorted((ROOT / "step/global").glob("*.step"))}
    if not {"rear_shell", "front_shell", "ref_protected_pack", "ref_lcd"} <= solids.keys():
        raise RuntimeError("Build the complete enclosure STEP set before checking.")
    results = {}
    for name, (footprint, design_height) in components.items():
        center = PORTS[name]["xy_mm"]
        component_top = PCB_BACK + design_height
        body = prism(center, footprint, PCB_BACK, component_top)
        if name == "SERVICE":
            # Clearance for a narrow insulated probe to push the slider both ways.
            reach = prism(center, (2.4, 5.8), component_top, CASE_TOP + 1.0)
        else:
            reach = cq.Solid.makeCylinder(1.0, CASE_TOP + 1.0 - component_top,
                                          cq.Vector(*center, component_top))
        hits = {}
        for part_name, solid in solids.items():
            body_overlap = body.intersect(solid).Volume()
            reach_overlap = reach.intersect(solid).Volume()
            if max(body_overlap, reach_overlap) > 1e-5:
                hits[part_name] = [body_overlap, reach_overlap]
        results[name] = {"center_case_xy_mm": center,
                         "assumed_body_height_including_allowance_mm": design_height,
                         "tool_depth_from_outside_to_assumed_top_mm": round(CASE_TOP - component_top, 3),
                         "overlaps_mm3": hits}
    report = {
        "units": "mm", "step_solids_checked": len(solids), "results": results,
        "physical_validation": "pending",
        "scope": "Rigid bodies, STEP geometry and nominal positions. Excludes wires, tolerances, switch forces and user handling.",
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                   [ROOT / "design/parameters.json", ROOT / "step/global/rear_shell.step",
                    ROOT / "stl/PRINT_rear_shell.stl"]},
    }
    (ROOT / "service-access.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if any(row["overlaps_mm3"] for row in results.values()):
        raise RuntimeError(f"Interference at service controls: {results}")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
