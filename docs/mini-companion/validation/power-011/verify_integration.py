"""Check actual charger-controller-system integration, not just gate equations."""
from pathlib import Path
import json,sys,re
from itertools import product
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from verify_system import read
r,p=read(H/'system-final.xml');oldr,old=read(H.parent/'power-010/system-final.xml')
def flat(p):return {k:v.removeprefix('charger/') for k,v in p.items()}
p=flat(p);old=flat(old)
assert p==flat(read(H/'before-format.xml')[1]),'Cosmetics changed netlist'
changes={k:(v,p.get(k)) for k,v in old.items() if p.get(k)!=v}
assert changes=={('U5','3'):('USB_3V3','VBUS_IN'),('U5','6'):('USB_3V3','VBUS_IN'),('C11','1'):('USB_3V3','VBUS_IN')},changes
cr,cp=read(H.parent/'power-004/core-final.xml')
def remap(ref):
 m=re.fullmatch(r'([URCJ])(\d+)',ref);assert m,ref
 return m[1]+str(int(m[2])+100)
expected={(remap(ref),pin):net for (ref,pin),net in cp.items()}
expected['R107','2']='VBUS_IN';expected['R108','2']='VBUS_IN'
for k,v in expected.items():assert p.get(k)==v,(k,v,p.get(k))
def switch_contract(p):
 assert [p['U7',str(i)] for i in range(1,9)]==['USB_EN1','EN_PULLDOWN_LINK','USB_READY','GND','EN_PULLDOWN_LINK','GND','CC_HIGH_QUALIFIED','VBUS_IN']
 assert p['U101','6']==p['U7','1']==p['R107','1']
 assert p['U101','5']==p['R108','1']=='USB_EN2'
 assert p['U101','10']==p['U101','11']==p['U1','10']=='SYS_RAW'
 assert p['U101','13']==p['U7','8']==p['U5','6']==p['U3','1']=='VBUS_IN'
 assert p['U101','2']==p['J102','1']=='PACK_POS'
 assert p['J102','2']=='GND' and p['J102','3']=='CELL_NTC'
 assert p['U3','5']!=p['U1','6'],'USB supply island merged into switched rail'
 assert p['C14','1']=='VBUS_IN' and p['C14','2']=='GND'
switch_contract(p)
for key,wrong in [(('U7','3'),'CC_HIGH_QUALIFIED'),(('J102','3'),'PACK_POS'),(('U101','10'),'PACK_POS')]:
 bad=dict(p);bad[key]=wrong
 try:switch_contract(bad)
 except AssertionError:pass
 else:raise AssertionError(('fault escaped',key))
values=lambda r:{c.attrib['ref']:c.findtext('value') for c in r.findall('./components/comp')}
v=values(r);ov=values(oldr);cv=values(cr)
assert len(v)==61
assert {k:(ov[k],v[k]) for k in ov if v[k]!=ov[k]}=={'R11':('100k 1%','22k 1%'),'R12':('10k 1%','47k 1%')}
for ref,value in cv.items():assert v[remap(ref)]==('10k 1%' if ref in ['R7','R8'] else value),(ref,value)
assert v['U7']=='TS5A23166DCUR'
erc=json.loads((H/'erc.json').read_text(encoding='utf-8'));assert not any(s['violations'] for s in erc['sheets'])
# Conditional steady-state checks at 4.5-5.5V TS supply; not brownout proof.
en_low=(5.5/9900+1e-6)*2*1.2
ready_high=3.07*.985-(5e-6+.3e-6+.02e-6)*22220
assert en_low<.4 and ready_high>2.4 and 10e-6*47470<.8
rows=[{'ready':a,'permission':b,'EN2':1,'EN1':0 if a and b else 1,'mode':'ILIM' if a and b else 'suspend'} for a,b in product([0,1],repeat=2)]
report={'status':'integrated_CC_only_review_not_release','components':len(v),'ERC_violations':0,'existing_pin_changes':{'.'.join(k):list(z) for k,z in changes.items()},'imported_core_contract':'pass with EN resistor low terminals moved GND to VBUS','faults_detected':3,'steady_state_control':rows,'conditional_EN1_low_V':en_low,'conditional_READY_high_V':ready_high,'Ioff_at_VCC_zero_output_V':10e-6*47470,'limitations':['TS 5V parameter table applies 4.5-5.5V; lower-input transition coverage incomplete','Supervisor falling delay has no guaranteed max; rapid brownout not validated','Default USB and BC1.2 not implemented','No physical safety, thermal, runtime or PCB verification']}
(H/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
