"""Independent coordinate transcription of TI drawing 4223750/D, top view."""
from pathlib import Path
import json
import math
import pcbnew as p

HERE = Path(__file__).resolve().parent
LIB = HERE.parents[3]/'hardware/candidates/system_power_review/MiniCompanionPower.pretty'
NAME = 'TI_DLA0010A_VSON-HR-10_2x3mm_P0.5mm'
fp = p.PCB_IO_KICAD_SEXPR().FootprintLoad(str(LIB), NAME)
assert fp is not None
# number: center x/y, width/height, mm. Physical ground extension is pad 8,
# not an eleventh exposed-pad number. Source PDF pages 36-37.
expected = {'1':(-.9,-1,.6,.25), '2':(-.9,-.5,.6,.25),
            '3':(-.9,0,.6,.25), '4':(-.9,.5,.6,.25), '5':(-.9,1,.6,.25),
            '6':(.75,1,.9,.25), '7':(.75,.5,.9,.25), '8':(.55,0,1.3,.25),
            '9':(.75,-.5,.9,.25), '10':(.75,-1,.9,.25)}
actual, apertures = {}, []
for pad in fp.Pads():
    pos,size = pad.GetPosition(),pad.GetSize()
    geometry = tuple(p.ToMM(v) for v in (pos.x,pos.y,size.x,size.y))
    if pad.IsOnLayer(p.F_Cu):
        assert pad.GetNumber() not in actual
        actual[pad.GetNumber()] = geometry
        assert pad.IsOnLayer(p.F_Mask)
        assert pad.IsOnLayer(p.F_Paste) == (pad.GetNumber() != '8')
        assert abs(pad.GetRoundRectRadiusRatio()-.2)<1e-6
    else:
        assert not pad.GetNumber() and pad.IsOnLayer(p.F_Paste)
        assert not pad.IsOnLayer(p.F_Mask)
        apertures.append(geometry)
assert actual.keys()==expected.keys()
for number in expected:
    assert all(abs(a-b)<1e-6 for a,b in zip(actual[number],expected[number])), number
assert sorted(apertures)==[(.175,0.0,.55,.25),(.925,0.0,.55,.25)]
# Rounded rectangle area rather than comparing bounding boxes alone.
area=lambda w,h:w*h-(4-math.pi)*.05**2
coverage=2*area(.55,.25)/area(1.3,.25)
assert .83 < coverage < .85
result={'source':'TI DLA0010A 4223750/D 03/2019 pp36-37',
        'copper_pad_count':len(actual),'numbering_and_geometry':'pass',
        'pad8_paste_apertures':apertures,'pad8_paste_coverage':coverage,
        'scope':'land and paste pattern check; no assembly/thermal release'}
(HERE/'footprint-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
