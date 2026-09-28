"""Verify host-permission integration; does not validate firmware or USB compliance."""
from pathlib import Path
from itertools import product
import sys,json
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from verify_system import read
r,p=read(H/'system-final.xml');oldr,old=read(H.parent/'power-012/system-final.xml')
assert p==read(H/'before-format.xml')[1],'Formatting changed nets'
changes={'.'.join(k):[v,p.get(k)] for k,v in old.items() if p.get(k)!=v}
assert changes=={'U6.3':['GND','USB_HOST_LOGIC']},changes
def contract(p):
 assert p['U6','3']==p['R19','2']==p['R20','1']=='USB_HOST_LOGIC'
 assert p['J8','1']==p['R19','1']=='HOST_USB_ALLOW'
 assert p['R20','2']==p['J8','2']=='GND'
 assert p['U7','3']==p['U6','1']=='USB_READY'
 assert p['U7','7']==p['U6','4']=='CC_HIGH_QUALIFIED'
 assert p['U6','6']=='CC_OUT1'
 assert p['U101','6']==p['U7','1']=='USB_EN1'
 assert p['U101','1']=='charger/TS' and p['J102','3']=='charger/CELL_NTC'
contract(p)
for k,n in [(('R20','2'),'USB_3V3'),(('U7','3'),'CC_HIGH_QUALIFIED'),(('U6','3'),'USB_3V3')]:
 bad=dict(p);bad[k]=n
 try:contract(bad)
 except AssertionError:pass
 else:raise AssertionError(('fault missed',k))
vals=lambda r:{c.attrib['ref']:c.findtext('value') for c in r.findall('./components/comp')}
v=vals(r);ov=vals(oldr);assert len(v)==74
assert {k:[value,v[k]] for k,value in ov.items() if value!=v[k]}=={'R105':['3.48k 1%','3.65k 1%']}
assert v['R19']=='470R 1%' and v['R20']=='10k 1%'
rows=[]
for ready,cc_out1,host in product([0,1],repeat=3):
 gate=host if cc_out1 else ready
 allow=ready and gate
 assert bool(allow)==bool(ready and (not cc_out1 or host))
 if not ready:assert not allow
 rows.append(dict(ready=ready,cc_out1=cc_out1,host=host,EN2=1,EN1=0 if allow else 1))
imax=1700/(3650*.99);reserve=.5-imax
assert reserve>.029
erc=json.loads((H/'erc.json').read_text(encoding='utf-8'));assert not any(s['violations'] for s in erc['sheets'])
report=dict(status='hardware_interface_candidate_only',components=74,ERC_violations=0,pin_changes=changes,
 faults_detected=3,truth_table=rows,input_current_A_min_typ_max=[1330/(3650*1.01),1512/3650,imax],
 remaining_from_500mA_A=reserve,
 conditional_floating_input_V_at_10uA=10e-6*10100,
 conditional_gate_high_V_with_3V_host=(3-5e-6*474.7)*9900/(9900+474.7),
 limits=['No MCU GPIO connected yet','GPIO levels need actual supply and drive guarantees; Schmitt thresholds at 3.3V not separately tabulated',
 'Host grant is software-trusted; stuck-high does not fail-safe for USB source permission',
 '29mA auxiliary allowance is a budget, not a measured or fully bounded current',
 'OFF Default USB, empty-battery SDP bootstrap and data isolation not completed',
 'Brownout, thermals and battery safety not physically validated'])
(H/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
