"""Allow exactly one electrical change versus HW-PWR-006: SW1.3 becomes NC."""
from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'power-006'))
from verify_system import read,contract
root,now=read(HERE/'system-final.xml')
_,before=read(HERE.parent/'power-006/system-final.xml')
changed={key:(before.get(key),now.get(key)) for key in before.keys()|now.keys()
         if before.get(key)!=now.get(key)}
assert changed=={('SW1','3'):('GND','unconnected-(SW1-C-Pad3)')},changed
check=dict(now);check['SW1','3']='GND';contract(check)
comps={c.attrib['ref']:c for c in root.findall('./components/comp')}
expected={
 'U1':('TPS63802DLAR','MiniCompanionPower:TI_DLA0010A_VSON-HR-10_2x3mm_P0.5mm'),
 'L1':('DFE201612E-R47M=P2','MiniCompanionPower:L_Murata_DFE201612E_2x1.6mm_H1.2mm'),
 'SW1':('PCM12SMTBR','Button_Switch_SMD:SW_SPDT_PCM12')}
for ref,(value,footprint) in expected.items():
    assert comps[ref].findtext('value')==value,ref
    assert comps[ref].findtext('footprint')==footprint,ref
erc=json.loads((HERE/'erc.json').read_text(encoding='utf-8'))
assert not any(s['violations'] for s in erc['sheets'])
# TI max EN leakage 0.2uA; use the specified 100k +1% corner.
assert comps['R3'].findtext('value')=='100k 1%'
ven_off=.2e-6*101000
assert ven_off<.4
report={'status':'review_revision_verified','components':len(comps),
        'connected_nets':len({v for v in now.values() if not v.startswith('unconnected-')}),
        'only_electrical_change':'SW1.3 GND -> explicit NC',
        'U1_L1_SW1_values_and_footprints':'pass','ERC_violations':0,
        'EN_off_V_with_0p2uA_and_101k':ven_off,
        'limitations':['switch lifetime and housing fit not verified',
                      'capacitor effective values and full power integration pending']}
(HERE/'revision-verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
