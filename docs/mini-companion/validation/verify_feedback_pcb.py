"""Verify feedback-only edits between KiCad 10 serialized boards.

Usage: python verify_feedback_pcb.py BEFORE AFTER REMOVAL_JSON
Filled copper and generated teardrops are recomputed by KiCad; compare manual
zone definitions separately and report generated-copper changes explicitly.
"""
import copy
import json
import sys
from collections import Counter
from pathlib import Path
from audit_pcb_roundtrip import read, objects

before, after = [read(p) for p in sys.argv[1:3]]
report = json.loads(Path(sys.argv[3]).read_text(encoding='utf-8'))
removed = {r['uuid'] for r in report['removed'] if r['type'] != 'ZONE'}
expected = copy.deepcopy(objects(before))
actual = objects(after)
for key, node in list(expected.items()):
    if key.startswith('zone:'):
        del expected[key]
        continue
    uid = next((n[1].strip('"') for n in node[1:] if isinstance(n, list) and n[0] == 'uuid'), None)
    if uid in removed:
        del expected[key]
        continue
    if node[0] == 'footprint' and ['property', '"Reference"', '"U101"'] == next(
            (n[:3] for n in node if isinstance(n, list) and n[:2] == ['property', '"Reference"']), None):
        for pad in node:
            if isinstance(pad, list) and pad[0] == 'pad' and pad[1].strip('"') in report['released_pads']:
                for field in pad:
                    if isinstance(field, list) and field[0] == 'net':
                        field[1] = json.dumps(report['released_pads'][pad[1].strip('"')])
actual = {k: v for k, v in actual.items() if not k.startswith('zone:')}
assert expected == actual, [k for k in expected.keys() | actual.keys() if expected.get(k) != actual.get(k)]

def zones(tree):
    return Counter(json.dumps([v for v in n if not isinstance(v, list) or v[0] not in
                               {'filled_polygon', 'filled_segments', 'fill_segments'}])
                   for n in tree[1:] if n[0] == 'zone')

a, b = zones(before), zones(after)
for serialized in (a - b).keys() | (b - a).keys():
    zone = json.loads(serialized)
    assert any(isinstance(n, list) and n[0] == 'attr' and 'teardrop' in str(n) for n in zone), 'Manual zone changed'
print(json.dumps({'pass': True, 'removed_nonzone_items': len(removed),
                  'old_teardrop_definitions_replaced_or_removed': sum((a - b).values()),
                  'new_teardrop_definitions': sum((b - a).values()),
                  'unchanged_remaining_nonzone_objects': True,
                  'unchanged_manual_zone_definitions': True,
                  'released_pads': report['released_pads']}, indent=2))
