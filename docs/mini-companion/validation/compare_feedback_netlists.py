"""Check that feedback removal preserves all other components and net endpoints.

Usage: python compare_feedback_netlists.py BEFORE.xml AFTER.xml
Inputs must be netlists exported by KiCad, not hand-written design approximations.
"""
import json
import sys
import xml.etree.ElementTree as ET

REMOVED = {"D401", "D402", "J401", "Q401", "R401", "R402", "TP104"}
RELEASED = {("U101", "33"), ("U101", "34")}


def read(path):
    root = ET.parse(path).getroot()
    components = {}
    for component in root.findall("./components/comp"):
        properties = sorted(
            (p.get("name"), p.get("value", ""))
            for p in component.findall("property")
            if p.get("name") in {"dnp", "exclude_from_board", "exclude_from_bom"}
        )
        components[component.get("ref")] = (
            component.findtext("value"), component.findtext("footprint"), properties
        )
    nets = {}
    released = {}
    for net in root.findall("./nets/net"):
        nodes = {(n.get("ref"), n.get("pin")) for n in net.findall("node")}
        for pin in RELEASED & nodes:
            released[pin] = nodes
        remaining = sorted(n for n in nodes if n[0] not in REMOVED and n not in RELEASED)
        if remaining:
            nets[net.get("name")] = remaining
    return components, nets, released


before, after = read(sys.argv[1]), read(sys.argv[2])
expected = {r: v for r, v in before[0].items() if r not in REMOVED}
errors = []
if expected != after[0]:
    errors.append({"component_changes": [
        r for r in sorted(set(expected) | set(after[0])) if expected.get(r) != after[0].get(r)
    ]})
if before[1] != after[1]:
    errors.append({"net_changes": [
        n for n in sorted(set(before[1]) | set(after[1]))
        if before[1].get(n) != after[1].get(n)
    ]})
for pin in sorted(RELEASED):
    if after[2].get(pin) != {pin}:
        errors.append({"gpio_not_isolated": list(pin)})
print(json.dumps({"pass": not errors, "errors": errors}, ensure_ascii=False, indent=2))
sys.exit(bool(errors))
