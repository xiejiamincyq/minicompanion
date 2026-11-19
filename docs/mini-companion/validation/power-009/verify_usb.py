"""Independent official pin-table contract; not USB compliance or analog proof."""
from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'power-006'))
from verify_system import read
root,p=read(HERE/'system-final.xml')
_,old=read(HERE.parent/'power-008/system-final.xml')
assert all(p.get(k)==v for k,v in old.items()),'Existing circuit changed'
assert p==read(HERE/'before-format.xml')[1],'Cleanup changed component connectivity'
def contract(p):
 for ref,pins in {
 'U3':{1:'VBUS_IN',2:'GND',5:'USB_3V3'},
 'U4':{1:'USB_CC1',2:'USB_CC2',3:'GND',4:'VBUS_DET',7:'CC_OUT1',8:'CC_OUT2',10:'GND',11:'GND',12:'USB_3V3'},
 'C8':{1:'VBUS_IN',2:'GND'},'C9':{1:'USB_3V3',2:'GND'},'C10':{1:'USB_3V3',2:'GND'},
 'R8':{1:'VBUS_IN',2:'VBUS_DET'},'R9':{1:'USB_3V3',2:'CC_OUT1'},'R10':{1:'USB_3V3',2:'CC_OUT2'},
 'J5':{1:'VBUS_IN',2:'USB_CC1',3:'USB_CC2',4:'GND'},'J6':{1:'CC_OUT1',2:'CC_OUT2',3:'GND'}}.items():
  for pin,net in pins.items():assert p[ref,str(pin)]==net,(ref,pin)
 for ref,pins in [('U3',[3,4]),('U4',[5,6,9])]:
  for pin in pins:assert p[ref,str(pin)].startswith('unconnected-'),(ref,pin)
 assert p['U3','5']!=p['U1','6'],'USB island shorted to MCU rail'
contract(p)
for target in [('U4','3'),('U3','1')]:
 bad=dict(p);bad[target]='USB_3V3'
 try:contract(bad)
 except AssertionError:pass
 else:raise AssertionError('Fault not detected')
v={c.attrib['ref']:c.findtext('value') for c in root.findall('./components/comp')}
assert len(v)==32
assert v['U3']=='TPS70933DBVR' and v['U4']=='TUSB320LAIRWBR'
assert v['R8']=='887k 1%' and v['R9']==v['R10']=='200k 1%'
assert 855e3<=887e3*.99<887e3*1.01<=920e3
erc=json.loads((HERE/'erc.json').read_text(encoding='utf-8'))
assert not any(s['violations'] for s in erc['sheets'])
report={'status':'detection_frontend_review_only','components':len(v),'ERC_violations':0,'existing_22_components':'pin connectivity unchanged','USB_pin_contract':'pass','wrong_PORT_and_LDO_input_faults':'detected','USB_island_separate_from_switched_rail':True,'VBUS_DET_resistor_ohm_range':[887e3*.99,887e3*1.01],'limitations':['Raw CC outputs are not charging permission','Worst-case auxiliary current and slow VBUS ramp not established','BC1.2, default USB and suspend policy not implemented','No physical measurements or PCB release']}
(HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
