"""Check the review-only charger core against its independent pin contract.

Run after exporting core-final.xml with the official KiCad CLI. Calculations
are conditional on the stated NTC resistance envelope and neglect TS leakage;
they are neither temperature certification nor permission to manufacture.
"""
from itertools import product
from pathlib import Path
import json
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent

# From TI SLUS937C p4-5, rather than the generated symbol cache.
U1_PINS = {
    '1': 'TS', '2': 'PACK_POS', '3': 'PACK_POS', '4': 'CHG_DISABLE',
    '5': 'USB_EN2', '6': 'USB_EN1', '7': 'PG_N', '8': 'GND',
    '9': 'CHG_N', '10': 'SYS_RAW', '11': 'SYS_RAW', '12': 'ILIM_SET',
    '13': 'VBUS_IN', '14': 'TMR_SET', '15': 'GND', '16': 'ICHG_SET',
    '17': 'GND',
}


def read_nets(path):
    tree = ET.parse(path)
    nets = {n.attrib['name'].removeprefix('/'): sorted((v.attrib['ref'], v.attrib['pin'])
            for v in n.findall('node')) for n in tree.findall('./nets/net')}
    return tree, nets


def check_contract(nets):
    pins = {(ref, pin): net for net, nodes in nets.items() for ref, pin in nodes}
    for pin, net in U1_PINS.items():
        assert pins.get(('U1', pin)) == net, ('U1', pin, pins.get(('U1', pin)), net)
    for ref, pair in {
        'R1': ('VBUS_IN', 'CELL_NTC'), 'R2': ('CELL_NTC', 'GND'),
        'R3': ('CELL_NTC', 'TS'), 'R4': ('ICHG_SET', 'GND'),
        'R5': ('ILIM_SET', 'GND'), 'R6': ('TMR_SET', 'GND'),
        'R7': ('USB_EN1', 'GND'), 'R8': ('USB_EN2', 'GND'),
        'R9': ('CHG_DISABLE', 'GND'),
        'R10': ('VLOGIC_SWITCHED', 'PG_N'),
        'R11': ('VLOGIC_SWITCHED', 'CHG_N'),
        'C1': ('VBUS_IN', 'GND'), 'C2': ('SYS_RAW', 'GND'),
        'C3': ('PACK_POS', 'GND'),
    }.items():
        assert tuple(pins.get((ref, str(p))) for p in (1, 2)) == pair, ref
    assert tuple(pins.get(('J2', str(p))) for p in (1, 2, 3)) == ('PACK_POS', 'GND', 'CELL_NTC')
    assert len(nets) == 15
    assert len(pins) == 59


def ratios(rntc):
    result = []
    for top_tol, bottom_tol, ntc_tol in product((.99, 1.01), (.99, 1.01), (.95, 1.05)):
        top, bottom = 39200 * top_tol, 30100 * bottom_tol
        ntc = rntc * ntc_tol
        low = bottom if ntc == float('inf') else bottom * ntc / (bottom + ntc)
        result.append(low / (top + low))
    return min(result), max(result)


if __name__ == '__main__':
    tree, nets = read_nets(BASE / 'core-final.xml')
    _, before = read_nets(BASE / 'core.xml')
    assert before == nets, 'Cosmetic changes altered connectivity'
    check_contract(nets)
    components = {c.attrib['ref']: c for c in tree.findall('./components/comp')}
    assert components['U1'].findtext('value') == 'BQ24072TRGTR'
    assert components['U1'].findtext('footprint') == 'Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm'
    assert components['R6'].findtext('value') == '71.5k 0.1%'
    # Confirm the contract catches a dangerous connector mix-up.
    bad = {n: [(r, '3' if p == '1' else '1' if p == '3' else p)
               if r == 'J2' else (r, p) for r, p in entries]
           for n, entries in nets.items()}
    try:
        check_contract(bad)
    except AssertionError:
        mutation_detected = True
    else:
        raise AssertionError('Connector fault escaped the independent contract')
    cold, hot, opened, shorted = [ratios(r) for r in (27280, 5827, float('inf'), 0)]
    assert cold[0] > .255 and hot[1] < .120
    assert opened[0] > .255 and shorted[1] < .120
    result = {
        'status': 'review_core_netlist_verified_not_manufacturing_release',
        'nets': len(nets), 'components': len(components),
        'cosmetic_connectivity_preserved': True,
        'battery_pin_swap_detected': mutation_detected,
        'ntc_assumption': '103AT nominal R(0C)/R(40C), each +/-5% procurement envelope; fixed resistors +/-1%; zero TS leakage',
        'cold_0C_ratio': cold, 'hot_40C_ratio': hot,
        'ntc_open_ratio': opened, 'ntc_short_ratio': shorted,
        'ichg_A_min_typ_max': [797/(2940*1.01), 890/2940, 975/(2940*.99)],
        'ilim_A_min_typ_max': [1330/(3480*1.01), 1512/3480, 1700/(3480*.99)],
        'timer_h_min_typ_max': [10*71.5*.999*35/3600, 10*71.5*45/3600, 10*71.5*1.001*55/3600],
        'limitations': ['USB source authorization unfinished', 'post-regulator and physical POWER not integrated',
                        'NTC pack and R-T envelope unconfirmed', 'TS leakage and real thermal response unverified',
                        'J1/J3/J4 are review interfaces, not production connectors'],
    }
    (BASE / 'core-verification.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
