"""Independent TI pin contract and DC budget; not a simulation or release check."""
import json
from pathlib import Path
from itertools import product
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent

def read(path):
    root = ET.parse(path)
    pins = {(n.attrib['ref'], n.attrib['pin']): net.attrib['name'].removeprefix('/')
            for net in root.findall('./nets/net') for n in net.findall('node')}
    return root, pins

def contract(p):
    # TI SLVSEU9D table 7-1, independently transcribed.
    expected = ['SYS_EN', 'GND', 'GND', 'FB', 'SYS_PG', 'VLOGIC_SWITCHED',
                'SW_L2', 'GND', 'SW_L1', 'SYS_RAW']
    assert [p['U1', str(i)] for i in range(1, 11)] == expected
    for ref, nets in {
        'L1': ['SW_L1', 'SW_L2'], 'C1': ['SYS_RAW', 'GND'],
        'C2': ['VLOGIC_SWITCHED', 'GND'], 'C3': ['VLOGIC_SWITCHED', 'GND'],
        'R1': ['VLOGIC_SWITCHED', 'FB'], 'R2': ['FB', 'GND'],
        'R3': ['SYS_EN', 'GND'], 'R4': ['VLOGIC_SWITCHED', 'SYS_PG'],
        'R5': ['VLOGIC_SWITCHED', 'GND'],
        'SW1': ['SYS_RAW', 'SYS_EN', 'GND'],
        'J1': ['SYS_RAW', 'GND'], 'J2': ['VLOGIC_SWITCHED', 'GND', 'SYS_PG'],
    }.items():
        assert [p[ref, str(i)] for i in range(1, len(nets)+1)] == nets, ref

if __name__ == '__main__':
    root, pins = read(HERE / 'system-final.xml')
    contract(pins)
    assert read(HERE / 'system.xml')[1] == pins, 'Layout changed connectivity'
    values = {c.attrib['ref']: c.findtext('value') for c in root.findall('./components/comp')}
    assert values['R1'] == '53.6k 0.1%' and values['R2'] == '10k 0.1%'
    assert len(values) == 13 and len(pins) == 36
    broken = dict(pins)
    broken['SW1', '1'], broken['SW1', '2'] = broken['SW1', '2'], broken['SW1', '1']
    try:
        contract(broken)
    except AssertionError:
        pass
    else:
        raise AssertionError('Wrong switch common pin not detected')
    # PWM reference +/-1%, resistors +/-0.1%, conservatively allow either
    # direction of the 100nA FB bias. PFM and transients are NOT bounded here.
    bounds = [.5*ref*(1+53600*hi/(10000*lo)) + bias*53600*hi
              for ref, hi, lo, bias in product((.99, 1.01), (.999, 1.001),
                                               (.999, 1.001), (-100e-9, 100e-9))]
    assert min(bounds) > 3.0 and max(bounds) < 3.3
    report = {'status': 'review_only_not_manufacturing_release', 'components':len(values),
              'pins':len(pins), 'nets':len(set(pins.values())),
              'netlist_and_switch_mutation_check': 'pass',
              'nominal_V':3.18, 'PWM_DC_V_min_max':[min(bounds), max(bounds)],
              'remaining_headroom_to_3V3_V':3.3-max(bounds),
              'limitations':['PFM ripple and transient peaks need verification',
                             'TPS63802 UVLO is not cell undervoltage protection',
                             'DLA footprint and exact passive/switch parts pending',
                             'USB/backlight/ADC integration and backfeed not verified',
                             '2A converter headline is not a system load guarantee']}
    (HERE/'verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
