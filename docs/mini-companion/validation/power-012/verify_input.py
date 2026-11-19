"""Input protection topology and conditional DC tolerances; no transient proof."""
from pathlib import Path
from itertools import product
import sys,json
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'power-006'))
from verify_system import read
r,p=read(H/'system-final.xml');oldr,old=read(H.parent/'power-011/system-final.xml')
changes={'.'.join(k):[v,p.get(k)] for k,v in old.items() if p.get(k)!=v}
assert changes=={'J5.1':['VBUS_IN','VBUS_RAW']},changes
before=read(H/'before-format.xml')[1]
assert {k:v for k,v in p.items() if k[0]!='R18'}==before,'Unexpected pin change during formatting'
def contract(p):
 expected={'U8':{1:'usb_input/INPUT_UVLO',2:'usb_input/INPUT_OVLO',5:'VBUS_RAW',6:'VBUS_IN',7:'usb_input/INPUT_SLEW',8:'GND',9:'usb_input/INPUT_ILIM'},
 'R13':{1:'VBUS_RAW',2:'usb_input/INPUT_OVLO'},'R14':{1:'usb_input/INPUT_OVLO',2:'GND'},
 'R15':{1:'VBUS_RAW',2:'usb_input/INPUT_UVLO'},'R16':{1:'usb_input/INPUT_UVLO',2:'GND'},
 'R17':{1:'usb_input/INPUT_ILIM',2:'GND'},'R18':{1:'VBUS_IN',2:'GND'},
 'C15':{1:'VBUS_RAW',2:'GND'},'C16':{1:'VBUS_IN',2:'GND'},'C17':{1:'usb_input/INPUT_SLEW',2:'GND'}}
 for ref,pins in expected.items():
  for pin,net in pins.items():assert p.get((ref,str(pin)))==net,(ref,pin,net,p.get((ref,str(pin))))
 assert p['J5','1']==p['U8','5']!=p['U8','6']
 assert p['U101','13']==p['U3','1']==p['U5','6']==p['U7','8']==p['U8','6']=='VBUS_IN'
 for pin in ['3','4','10']:assert p['U8',pin].startswith('unconnected-'),pin
contract(p)
for key,wrong in [(('U8','6'),'VBUS_RAW'),(('U101','13'),'VBUS_RAW'),(('R13','2'),'usb_input/INPUT_UVLO')]:
 bad=dict(p);bad[key]=wrong
 try:contract(bad)
 except AssertionError:pass
 else:raise AssertionError(('fault missed',key))
values=lambda r:{c.attrib['ref']:c.findtext('value') for c in r.findall('./components/comp')}
v=values(r);assert len(v)==71
assert all(v[k]==value for k,value in values(oldr).items())
assert {k:v[k] for k in ['U8','R13','R14','R15','R16','R17','R18','C15','C16','C17']}==dict(U8='TPS259470LRPWR',R13='34.8k 0.1%',R14='10k 0.1%',R15='27.4k 0.1%',R16='10k 0.1%',R17='3.32k 0.1%',R18='100k 1%',C15='1uF 50V X7R',C16='2.2uF 10V X7R',C17='2.2nF 5% 50V C0G')
def bounds(top,thresholds):
 a=[vt*(1+top*rt/(10000*rb))+leak*top*rt for vt,rt,rb,leak in product(thresholds,[.999,1.001],[.999,1.001],[-.1e-6,.1e-6])]
 return [min(a),max(a)]
ov=bounds(34800,[1.183,1.223]);uv=bounds(27400,[1.183,1.223])
assert ov[0]>5.25 and ov[1]<5.5 and uv[1]<4.75
erc=json.loads((H/'erc.json').read_text(encoding='utf-8'));assert not any(s['violations'] for s in erc['sheets'])
report=dict(status='candidate_only',components=71,ERC_violations=0,old_pin_changes=changes,faults_detected=3,
 OV_rising_V=ov,OV_falling_V=bounds(34800,[1.076,1.116]),UV_rising_V=uv,UV_falling_V=bounds(27400,[1.076,1.116]),
 ILIM_A_table_at_3320ohm=[.85,1.15],ILIM_A_resistance_scaled_estimate=[.85/1.001,1.15/.999],
 divider_current_5V_typ_A=5/44800+5/37400,bleed_current_5V_typ_A=5/100000,
 slew_5V_nominal_ms=5*2200/2000,
 limitations=['DC thresholds are not transient voltage bounds','UV falling below 4.5V does not close gate brownout gap','OVLO recovery bypasses dVdt','No 28V or reverse-input system rating','No certified USB Default/BC1.2 path','Footprint, capacitor MPNs, surge/ESD, price and bench tests pending'])
(H/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
