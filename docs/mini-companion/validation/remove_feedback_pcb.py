"""Produce a feedback-free candidate using the official KiCad pcbnew API.

Run with KiCad's Python: INPUT OUTPUT NETLIST_XML. Never edits INPUT.
Only explicitly audited dead power branches are removed from shared nets.
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew

source, output, netlist = map(Path, sys.argv[1:])
assert source.resolve() != output.resolve()
assert not output.exists(), 'Refuse to overwrite an existing candidate'
board = pcbnew.LoadBoard(str(source))
refs = {'D401', 'D402', 'J401', 'Q401', 'R401', 'R402', 'TP104'}
nets = {'LED_PWM', 'MOTOR_PWM', 'Net-(D401-A)', 'Net-(D402-A)'}
found = {f.GetReference() for f in board.GetFootprints()} & refs
assert found == refs, found
removed = []
# Retain the SWIG containers and removed wrappers until SaveBoard completes.
footprints = board.GetFootprints()
tracks = board.GetTracks()
zones = board.Zones()
items = list(tracks) + list(zones)
footprint_items = list(footprints)
dead_branches = {
    '12a4117c-6655-425d-860e-a11dad3e77d6',  # D401+ to dedicated via
    '05113319-e234-4c9f-9aaf-884817a5d8b0',  # dedicated +BATT via
    '7e9d646e-b3bd-434d-b5ce-e1655bbe6f1b',  # via to J401+ branch
    'a7b0193e-6e1a-4d02-b95a-67c308b145fc',  # J401+ final segment
    '54e58fa7-f9d3-43c7-9893-e1041ddb6e62',  # dead branch toward shared junction
    'c5f94a35-c527-4ed9-aa2d-c4ff3cfc364c',
    '34d77809-534b-426a-a981-74771c3600b3',  # stop at 134.75,87.75 shared junction
    '60be0037-8fe6-4694-a0e0-8aac4385cf36',  # Q401 ground stub
    'ac6fecc7-5b8c-4d77-a507-1cedd1b490c8',  # R402 ground stub
}
assert dead_branches <= {t.m_Uuid.AsString() for t in tracks}
dead_points = [(p.GetNetname(), p.GetPosition()) for f in footprint_items
               if f.GetReference() in refs for p in f.Pads()
               if p.GetNetname() in {'GND', '+BATT'}]
for t in tracks:
    if t.m_Uuid.AsString() in dead_branches:
        dead_points.extend([(t.GetNetname(), t.GetStart()), (t.GetNetname(), t.GetEnd())])
for item in items:
    dead_teardrop = (isinstance(item, pcbnew.ZONE) and item.IsTeardropArea()
                    and any(item.GetNetname() == n and item.Outline().Contains(p)
                            for n, p in dead_points))
    if item.GetNetname() in nets or item.m_Uuid.AsString() in dead_branches or dead_teardrop:
        removed.append({'uuid': item.m_Uuid.AsString(), 'type': item.GetClass(), 'net': item.GetNetname()})
        board.Remove(item)
for footprint in footprint_items:
    if footprint.GetReference() in refs:
        removed.append({'uuid': footprint.m_Uuid.AsString(), 'ref': footprint.GetReference(), 'type': 'FOOTPRINT'})
        board.Remove(footprint)
root = ET.parse(netlist).getroot()
names = {}
for net in root.findall('./nets/net'):
    for node in net.findall('node'):
        if node.get('ref') == 'U101' and node.get('pin') in {'33', '34'}:
            assert len(net.findall('node')) == 1
            names[node.get('pin')] = net.get('name')
assert len(names) == 2
for footprint in board.GetFootprints():
    if footprint.GetReference() == 'U101':
        for pad in footprint.Pads():
            if pad.GetNumber() in names:
                net = pcbnew.NETINFO_ITEM(board, names[pad.GetNumber()])
                board.Add(net)
                pad.SetNet(net)
pcbnew.SaveBoard(str(output), board)
report = output.with_suffix('.removal.json')
report.write_text(json.dumps({'removed': removed, 'released_pads': names}, indent=2) + '\n', encoding='utf-8')
print(str(report))
